"""Shared harness code: keys, HTTP with backoff, spend ledger, request builders and answer parsers.

Keys are read from the repository's .env at runtime and live only in this process's memory. They are
never printed, logged or written; every saved request or header set passes through `scrub`.
"""
from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

DEMO = Path(__file__).resolve().parent
ROOT = DEMO.parents[3]          # repository root
DEC = DEMO.parent               # .studio/ai-channel/decisions
SAMPLES = DEC / "data" / "samples"
RESULTS = DEMO / "results"
LOGS = DEMO / "logs"
EVIDENCE = DEMO / "evidence"
for _d in (RESULTS, LOGS, EVIDENCE):
    _d.mkdir(exist_ok=True)

CAP_USD = 5.00
KEY_NAMES = {"google": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY", "jev": "JEV_API_KEY"}

# Published prices, USD per 1M tokens, read 2026-11-14 (see REPORT.md provenance).
PRICES = {
    "gemini-decision-1": {"input": 0.10},
    "gemini-4-hydrogen": {"input": 1.50, "output": 7.50},
    "gpt-6-luna/decisions": {"input": 0.10, "cached": 0.01, "cache_write": 0.125},
    "gpt-6-luna/responses": {"input": 0.10, "cached": 0.01, "cache_write": 0.125, "output": 0.50},
    "jev-1.14.0": {"input": 0.042},
}

MODELS = {
    "google": {"decisions": "gemini-decision-1", "generative": "gemini-4-hydrogen"},
    "openai": {"decisions": "gpt-6-luna", "generative": "gpt-6-luna"},
    "jev": {"decisions": "jev-1.14.0"},
}
ENDPOINTS = {
    ("google", "decisions"): "https://generativelanguage.googleapis.com/v1beta/decisions",
    ("google", "generative"): "https://generativelanguage.googleapis.com/v1beta/interactions",
    ("openai", "decisions"): "https://api.openai.com/v1/decisions",
    ("openai", "generative"): "https://api.openai.com/v1/responses",
    ("jev", "decisions"): "https://api.typesafe.ai/v1/systemone",
}
GOOGLE_API_REVISION = "2026-05-20"   # the Api-Revision header shown in the Interactions docs examples

# ---------------------------------------------------------------- keys and scrubbing

_KEYS: dict[str, str] = {}


def load_key(provider: str) -> str:
    name = KEY_NAMES[provider]
    if name not in _KEYS:
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[7:].strip()
            if line.startswith(name + "="):
                v = line.split("=", 1)[1].strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                _KEYS[name] = v
                break
        else:
            raise SystemExit(f"{name} not found in .env")
    return _KEYS[name]


SENSITIVE_HEADERS = {"cf-ray", "x-amz-cf-pop", "via", "authorization", "x-goog-api-key", "cookie", "set-cookie", "x-api-key", "api-key",
                     "openai-organization", "openai-project", "x-goog-user-project"}


def scrub(obj):
    """Return a copy with every loaded key value replaced, recursively."""
    if isinstance(obj, str):
        for v in _KEYS.values():
            if v and v in obj:
                obj = obj.replace(v, "[REDACTED]")
        return obj
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [scrub(v) for v in obj]
    return obj


def safe_headers(headers) -> dict:
    return scrub({k.lower(): v for k, v in headers.items() if k.lower() not in SENSITIVE_HEADERS})


REQUEST_ID_HEADERS = ("x-request-id", "request-id", "x-goog-request-id", "x-cloud-trace-context",
                      "x-typesafe-request-id", "typesafe-request-id", "openai-processing-ms", "server-timing",
                      "server-timing-total", "x-envoy-upstream-service-time")


def request_ids(headers) -> dict:
    h = {k.lower(): v for k, v in headers.items()}
    return {k: h[k] for k in REQUEST_ID_HEADERS if k in h}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def log(name: str, msg: str) -> None:
    line = f"{now()} {msg}"
    print(line, flush=True)
    with (LOGS / f"{name}.log").open("a") as f:
        f.write(scrub(line).replace(str(ROOT), ".") + "\n")


# ---------------------------------------------------------------- spend ledger

class Ledger:
    """Append-only spend ledger per provider, computed from response usage and published prices."""

    def __init__(self, provider: str):
        self.provider = provider
        self.path = RESULTS / f"ledger-{provider}.jsonl"
        self.spent = 0.0
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    self.spent += json.loads(line)["cost_usd"]

    def check(self, estimate: float) -> None:
        if self.spent + estimate > CAP_USD:
            raise CapReached(f"{self.provider}: spent {self.spent:.6f} + estimate {estimate:.6f} > cap {CAP_USD}")

    def add(self, cost: float, tag: str) -> None:
        self.spent += cost
        with self.path.open("a") as f:
            f.write(json.dumps({"t": now(), "tag": tag, "cost_usd": cost, "total_usd": self.spent}) + "\n")


class CapReached(Exception):
    pass


def cost_of(price_key: str, usage: dict) -> tuple[float, dict]:
    """Cost in USD and the billed token breakdown, from a provider's usage object."""
    p = PRICES[price_key]
    if price_key == "gemini-decision-1":
        tin = int(usage.get("total_input_tokens", 0))
        return tin * p["input"] / 1e6, {"input": tin, "output": int(usage.get("total_output_tokens", 0))}
    if price_key == "jev-1.14.0":
        tin = int(usage.get("input_tokens", 0))
        return tin * p["input"] / 1e6, {"input": tin, "output_free": int(usage.get("output_tokens", 0))}
    if price_key.startswith("gpt-6-luna"):
        tin = int(usage.get("input_tokens", 0))
        det = usage.get("input_tokens_details") or {}
        cached = int(det.get("cached_tokens") or 0)
        write = int(det.get("cache_write_tokens") or 0)
        out = int(usage.get("output_tokens", 0))
        c = (tin - cached - write) * p["input"] + cached * p["cached"] + write * p["cache_write"]
        if "output" in p:
            c += out * p["output"]
        return c / 1e6, {"input": tin, "cached": cached, "cache_write": write, "output": out,
                         "reasoning": int((usage.get("output_tokens_details") or {}).get("reasoning_tokens") or 0)}
    if price_key == "gemini-4-hydrogen":
        tin = int(usage.get("total_input_tokens", 0))
        cached = int(usage.get("total_cached_tokens", 0) or 0)
        out = int(usage.get("total_output_tokens", 0))
        thought = int(usage.get("total_thought_tokens", 0) or 0)
        c = (tin - cached) * p["input"] + cached * 0.075 + (out + thought) * p["output"]
        return c / 1e6, {"input": tin, "cached": cached, "output": out, "thought": thought}
    raise KeyError(price_key)


# ---------------------------------------------------------------- HTTP

@dataclass
class Reply:
    status: int
    body: dict | None
    text: str
    headers: dict
    latency_ms: float
    attempts: int
    request_ids: dict


class Http:
    def __init__(self, provider: str):
        self.provider = provider
        self.client = httpx.Client(timeout=httpx.Timeout(120.0, connect=20.0), http2=False)

    def auth_headers(self) -> dict:
        key = load_key(self.provider)
        if self.provider == "google":
            return {"x-goog-api-key": key, "Api-Revision": GOOGLE_API_REVISION}
        return {"Authorization": f"Bearer {key}"}

    def post(self, url: str, payload: dict, logname: str) -> Reply:
        headers = {"Content-Type": "application/json", **self.auth_headers()}
        data = json.dumps(payload).encode()
        delay = 2.0
        for attempt in range(1, 8):
            t0 = time.perf_counter()
            try:
                r = self.client.post(url, content=data, headers=headers)
                dt = (time.perf_counter() - t0) * 1000
            except httpx.HTTPError as e:
                log(logname, f"transport error attempt {attempt}: {type(e).__name__}")
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            if r.status_code in (429, 500, 502, 503, 504, 529):
                ra = r.headers.get("retry-after")
                wait = float(ra) if ra and ra.replace(".", "").isdigit() else delay
                # Google's free tier once sent retry-after 59327 s and answered again minutes later: cap the wait.
                wait = min(wait, 300.0)
                log(logname, f"HTTP {r.status_code} attempt {attempt}; backing off {wait:.1f}s (retry-after {ra}); ids={request_ids(r.headers)}; body={r.text[:300]!r}")
                time.sleep(wait + random.random())
                delay = min(delay * 2, 60)
                continue
            try:
                body = r.json()
            except ValueError:
                body = None
            return Reply(r.status_code, body, r.text, safe_headers(r.headers), dt, attempt, request_ids(r.headers))
        return Reply(-1, None, "gave up after retries", {}, -1, attempt, {})


# ---------------------------------------------------------------- task definitions

SCORE_LEVELS = ["Very negative", "Negative", "Neutral", "Positive", "Very positive"]
CHOICE_INSTR = "Which banking customer-support intent does this customer message express?"
SCORE_INSTR = "How positive is the sentiment of this movie-review sentence?"


def option_key(label: str) -> str:
    return label.lower().rstrip("?")


def label_desc(label: str) -> str:
    return option_key(label).replace("_", " ")


def load_set(name: str) -> list[dict]:
    return [json.loads(line) for line in (SAMPLES / f"{name}.jsonl").read_text().splitlines() if line.strip()]


def banking_labels() -> list[str]:
    return json.loads((SAMPLES / "meta.json").read_text())["sets"]["choice"]["labels"]


def predicate_instr(question: str) -> str:
    q = question.strip().rstrip("?")
    return f"According to the passage, {q}?"


def item_input(task: str, item: dict) -> str:
    if task == "predicate":
        return item["passage"]
    return item["text"]


@dataclass
class Q:
    """A provider-neutral question."""
    name: str
    type: str                  # predicate | choice | score
    instructions: str
    options: list[str] | None = None        # option keys (choice) or level texts (score)
    descriptions: list[str] | None = None   # choice descriptions


def task_question(task: str, item: dict, labels: list[str] | None = None) -> Q:
    if task == "choice":
        keys = [option_key(x) for x in labels]
        return Q("intent", "choice", CHOICE_INSTR, keys, [label_desc(x) for x in labels])
    if task == "predicate":
        return Q("answer_yes", "predicate", predicate_instr(item["question"]))
    if task == "score":
        return Q("sentiment", "score", SCORE_INSTR, SCORE_LEVELS)
    raise KeyError(task)


def build_decision(provider: str, text: str, questions: list[Q]) -> dict:
    model = MODELS[provider]["decisions"]
    if provider == "openai":
        qs = []
        for q in questions:
            d = {"type": q.type, "name": q.name, "instructions": q.instructions}
            if q.type == "choice":
                d["choices"] = [{"value": k, "description": desc} for k, desc in zip(q.options, q.descriptions)]
            elif q.type == "score":
                d["levels"] = [{"label": lv} for lv in q.options]
            qs.append(d)
        return {"model": model, "input": text, "questions": qs}
    qs = {}
    for q in questions:
        t = "noul" if q.type == "predicate" else q.type
        d = {"type": t, "instructions": q.instructions}
        if q.type == "choice":
            d["criteria"] = {k: desc for k, desc in zip(q.options, q.descriptions)}
        elif q.type == "score":
            d["criteria"] = list(q.options)
        qs[q.name] = d
    key = "state" if provider == "jev" else "input"
    return {"model": model, key: text, "questions": qs}


def parse_decision(provider: str, body: dict, questions: list[Q]) -> list[dict]:
    """Normalise answers: for each question, {name, kind, p_yes | probs, pred, api_confidence, refusal}."""
    out = []
    if provider == "openai":
        by_name = {a.get("name"): a for a in body.get("answers", [])}
    else:
        by_name = body.get("answers", {})
    for q in questions:
        a = by_name.get(q.name)
        rec = {"name": q.name, "type": q.type, "refusal": False, "api_confidence": None}
        if a is None:
            rec["missing"] = True
            out.append(rec)
            continue
        if a.get("type") == "refusal":
            rec["refusal"] = True
            out.append(rec)
            continue
        if q.type == "predicate":
            p = a.get("probability") if provider == "openai" else a.get("noul")
            rec["p_yes"] = float(p)
            rec["pred"] = rec["p_yes"] >= 0.5
            rec["api_confidence"] = a.get("confidence")
        elif q.type == "choice":
            probs = a.get("probabilities")
            if isinstance(probs, list):
                probs = {str(x["value"]): float(x["probability"]) for x in probs}
            rec["probs"] = {k: float(v) for k, v in probs.items()}
            rec["pred"] = str(a.get("choice"))
            rec["api_confidence"] = a.get("confidence")
        elif q.type == "score":
            probs = a.get("probabilities")
            if isinstance(probs, list):
                probs = {str(x["value"]): float(x["probability"]) for x in probs}
            rec["probs"] = {str(k): float(v) for k, v in probs.items()}
            rec["expected"] = a.get("score")
            rec["pred"] = int(max(rec["probs"], key=rec["probs"].get))
            rec["api_confidence"] = a.get("confidence")
        out.append(rec)
    return out


def decision_usage(provider: str, body: dict) -> tuple[str, dict]:
    pk = {"google": "gemini-decision-1", "openai": "gpt-6-luna/decisions", "jev": "jev-1.14.0"}[provider]
    return pk, (body.get("usage") if isinstance(body, dict) else None) or {}


# ---------------------------------------------------------------- generative baseline

def gen_prompt(text: str, labels: list[str]) -> str:
    keys = "\n".join(f"- {option_key(x)}" for x in labels)
    return (
        "Classify the customer message into exactly one banking customer-support intent from the list.\n"
        "Return JSON with two fields: \"label\" (one intent from the list, copied exactly) and "
        "\"probability\" (your probability, from 0 to 1, that the label is correct).\n\n"
        f"Intents:\n{keys}\n\nCustomer message:\n{text}"
    )


def gen_schema(labels: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "label": {"type": "string", "enum": [option_key(x) for x in labels]},
            "probability": {"type": "number"},
        },
        "required": ["label", "probability"],
        "additionalProperties": False,
    }


def build_generative(provider: str, text: str, labels: list[str]) -> dict:
    prompt = gen_prompt(text, labels)
    if provider == "openai":
        return {
            "model": MODELS["openai"]["generative"],
            "input": prompt,
            "reasoning": {"effort": "none"},
            "store": False,
            "max_output_tokens": 400,
            "text": {"format": {"type": "json_schema", "name": "intent", "strict": True, "schema": gen_schema(labels)}},
        }
    return {
        "model": MODELS["google"]["generative"],
        "input": prompt,
        "store": False,
        "generation_config": {"thinking_level": "low", "max_output_tokens": 4096},
        "response_format": {"type": "text", "mime_type": "application/json", "schema": gen_schema(labels)},
    }


def generative_text(provider: str, body: dict) -> str | None:
    if provider == "openai":
        for item in body.get("output", []) or []:
            if item.get("type") == "message":
                for c in item.get("content", []) or []:
                    if c.get("type") == "output_text":
                        return c.get("text")
                    if c.get("type") == "refusal":
                        return None
        return body.get("output_text")
    # Interactions API: look for the model output text in the returned steps/outputs.
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    for key in ("outputs", "steps", "output"):
        for step in body.get(key, []) or []:
            if not isinstance(step, dict):
                continue
            if step.get("type") in ("text", "model_output") and isinstance(step.get("text"), str):
                return step["text"]
            for c in step.get("content", []) or []:
                if isinstance(c, dict) and c.get("type") == "text" and isinstance(c.get("text"), str):
                    return c["text"]
    return None


def parse_generative(provider: str, body: dict, labels: list[str]) -> dict:
    txt = generative_text(provider, body)
    rec = {"raw_text": txt, "parse_ok": False, "refusal": txt is None}
    if txt is None:
        return rec
    try:
        m = re.search(r"\{.*\}", txt, re.S)
        j = json.loads(m.group(0) if m else txt)
        rec["pred"] = str(j["label"])
        rec["stated_p"] = float(j["probability"])
        rec["parse_ok"] = rec["pred"] in {option_key(x) for x in labels} and 0 <= rec["stated_p"] <= 1
    except Exception as e:  # noqa: BLE001
        rec["parse_error"] = type(e).__name__
    return rec


def generative_usage(provider: str, body: dict) -> tuple[str, dict]:
    u = (body.get("usage") if isinstance(body, dict) else None) or {}
    return ("gpt-6-luna/responses" if provider == "openai" else "gemini-4-hydrogen"), u
