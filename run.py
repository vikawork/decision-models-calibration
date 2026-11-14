"""Measured runs. Sequential requests per provider; resumable (items already recorded with HTTP 200 are skipped).

  python -I run.py <provider> decisions <choice|predicate|score>
  python -I run.py <provider> pair                       # choice set: decisions and generative, interleaved per item
  python -I run.py <provider> fanout                     # 1, 10, 50, 200 questions on one shared passage, 5 repeats

Writes results/<provider>-<api>-<set>.jsonl (one line per request).
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder; add only our own code
from common import (ENDPOINTS, MODELS, PRICES, RESULTS, CapReached, Http, Ledger, Q, banking_labels,
                    build_decision, build_generative, cost_of, decision_usage, generative_usage, load_set, log,
                    now, parse_decision, parse_generative, scrub, task_question, item_input)

FANOUT_SIZES = [1, 10, 50, 200]
FANOUT_REPEATS = 5
SEED = 20261114


def out_path(provider: str, api: str, name: str) -> Path:
    return RESULTS / f"{provider}-{api}-{name}.jsonl"


def done_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r["status"] == 200 or r.get("final"):
                ids.add(r["id"])
    return ids


def estimate(price_key: str, payload: dict, max_out: int = 0) -> float:
    p = PRICES[price_key]
    toks = len(json.dumps(payload)) / 2.5
    return (toks * max(p.get("input", 0), p.get("cache_write", 0)) + max_out * p.get("output", 0)) / 1e6


def call(http: Http, led: Ledger, provider: str, api: str, payload: dict, logname: str, tag: str):
    pk = {("google", "decisions"): "gemini-decision-1", ("google", "generative"): "gemini-4-hydrogen",
          ("openai", "decisions"): "gpt-6-luna/decisions", ("openai", "generative"): "gpt-6-luna/responses",
          ("jev", "decisions"): "jev-1.14.0"}[(provider, api)]
    max_out = (payload.get("max_output_tokens") or (payload.get("generation_config") or {}).get("max_output_tokens") or 0)
    led.check(estimate(pk, payload, max_out))
    rep = http.post(ENDPOINTS[(provider, api)], payload, logname)
    usage_key, usage = (decision_usage if api == "decisions" else generative_usage)(provider, rep.body)
    cost, billed = cost_of(usage_key, usage) if rep.status == 200 else (0.0, {})
    led.add(cost, tag)
    return rep, usage, cost, billed


def base_record(provider, api, name, item_id, rep, usage, cost, billed):
    rec = {
        "t": now(), "provider": provider, "api": api, "model": MODELS[provider][api], "set": name, "id": item_id,
        "status": rep.status, "latency_ms": rep.latency_ms, "attempts": rep.attempts, "request_ids": rep.request_ids,
        "usage": usage, "billed": billed, "cost_usd": cost,
        "returned_model": rep.body.get("model") if isinstance(rep.body, dict) else None,
    }
    if rep.status != 200:
        rec["error"] = (json.dumps(rep.body) if rep.body is not None else rep.text)[:1500]
        rec["final"] = rep.status in (400, 401, 402, 403, 404, 413, 422)
    return rec


def write(path: Path, rec: dict) -> None:
    with path.open("a") as f:
        f.write(json.dumps(scrub(rec)) + "\n")


def run_decisions(provider: str, task: str) -> None:
    items = load_set(task)
    labels = banking_labels() if task == "choice" else None
    path = out_path(provider, "decisions", task)
    skip = done_ids(path)
    http, led = Http(provider), Ledger(provider)
    logname = f"run-{provider}"
    log(logname, f"decisions {task}: {len(items) - len(skip)} to do, spent so far {led.spent:.6f}")
    for n, item in enumerate(items):
        if item["id"] in skip:
            continue
        q = task_question(task, item, labels)
        payload = build_decision(provider, item_input(task, item), [q])
        rep, usage, cost, billed = call(http, led, provider, "decisions", payload, logname, f"decisions-{task}")
        rec = base_record(provider, "decisions", task, item["id"], rep, usage, cost, billed)
        rec["gold"] = item["gold"]
        if rep.status == 200:
            rec["answer"] = parse_decision(provider, rep.body, [q])[0]
        write(path, rec)
        if rep.status != 200:
            log(logname, f"{item['id']} HTTP {rep.status}: {rec.get('error', '')[:300]}")
            if rep.status in (401, 402, 403):
                raise SystemExit(f"stopping {provider}: HTTP {rep.status}")
        if n % 50 == 0:
            log(logname, f"decisions {task} {n}/{len(items)} last {rep.latency_ms:.0f} ms spent {led.spent:.6f}")
    log(logname, f"decisions {task} done; spent {led.spent:.6f}")


def run_pair(provider: str) -> None:
    """Choice set through the decision API and the generative baseline, alternating which goes first."""
    items = load_set("choice")
    labels = banking_labels()
    pd, pg = out_path(provider, "decisions", "choice"), out_path(provider, "generative", "choice")
    sd, sg = done_ids(pd), done_ids(pg)
    http, led = Http(provider), Ledger(provider)
    logname = f"run-{provider}"
    log(logname, f"pair: {len(items)} items, spent so far {led.spent:.6f}")
    for n, item in enumerate(items):
        order = ["decisions", "generative"] if n % 2 == 0 else ["generative", "decisions"]
        for api in order:
            if item["id"] in (sd if api == "decisions" else sg):
                continue
            if api == "decisions":
                q = task_question("choice", item, labels)
                payload = build_decision(provider, item["text"], [q])
            else:
                payload = build_generative(provider, item["text"], labels)
            rep, usage, cost, billed = call(http, led, provider, api, payload, logname, f"{api}-choice")
            rec = base_record(provider, api, "choice", item["id"], rep, usage, cost, billed)
            rec["gold"] = item["gold"]
            rec["order"] = order.index(api)
            if rep.status == 200:
                rec["answer"] = (parse_decision(provider, rep.body, [q])[0] if api == "decisions"
                                 else parse_generative(provider, rep.body, labels))
            write(pd if api == "decisions" else pg, rec)
            if rep.status != 200:
                log(logname, f"{api} {item['id']} HTTP {rep.status}: {rec.get('error', '')[:300]}")
                if rep.status in (401, 402, 403):
                    raise SystemExit(f"stopping {provider}: HTTP {rep.status}")
        if n % 25 == 0:
            log(logname, f"pair {n}/{len(items)} spent {led.spent:.6f}")
    log(logname, f"pair done; spent {led.spent:.6f}")


def fanout_fixture() -> dict:
    """One shared passage and 200 checkable questions: does the passage contain word X (100 yes, 100 no)."""
    items = load_set("predicate")
    host = max(items, key=lambda r: len(r["passage"].split()))
    text = host["passage"]
    low = text.lower()
    toks = re.findall(r"[a-z]+", low)
    present, seen = [], set()
    for w in toks:
        if len(w) >= 5 and w not in seen:
            seen.add(w)
            present.append(w)
    others = []
    for r in items:
        if r["id"] == host["id"]:
            continue
        for w in re.findall(r"[a-z]+", r["passage"].lower()):
            if len(w) >= 6 and w not in low and w not in others:
                others.append(w)
    rng = random.Random(SEED)
    present = rng.sample(present, 100) if len(present) >= 100 else present
    absent = rng.sample(others, 200 - len(present))
    words = []
    for a, b in zip(present, absent):
        words += [(a, True), (b, False)]
    words += [(b, False) for b in absent[len(present):]]
    qs = [{"name": f"w{i:03d}", "word": w, "gold": g} for i, (w, g) in enumerate(words)]
    return {"host_id": host["id"], "passage": text, "questions": qs}


def run_fanout(provider: str) -> None:
    fx = fanout_fixture()
    (RESULTS / "fanout-fixture.json").write_text(json.dumps(fx, indent=1))
    path = out_path(provider, "decisions", "fanout")
    skip = done_ids(path)
    http, led = Http(provider), Ledger(provider)
    logname = f"run-{provider}"
    for r in range(FANOUT_REPEATS):
        sizes = FANOUT_SIZES[r % 4:] + FANOUT_SIZES[:r % 4]
        for k in sizes:
            rid = f"n{k}-r{r}"
            if rid in skip:
                continue
            qs = [Q(q["name"], "predicate", f"Does the passage contain the word \"{q['word']}\"?") for q in fx["questions"][:k]]
            payload = build_decision(provider, fx["passage"], qs)
            rep, usage, cost, billed = call(http, led, provider, "decisions", payload, logname, f"fanout-{k}")
            rec = base_record(provider, "decisions", "fanout", rid, rep, usage, cost, billed)
            rec.update({"n_questions": k, "repeat": r})
            if rep.status == 200:
                ans = parse_decision(provider, rep.body, qs)
                gold = {q["name"]: q["gold"] for q in fx["questions"][:k]}
                rec["answers"] = [{"name": a["name"], "p_yes": a.get("p_yes"), "refusal": a["refusal"],
                                   "gold": gold[a["name"]]} for a in ans]
            write(path, rec)
            log(logname, f"fanout {rid} HTTP {rep.status} {rep.latency_ms:.0f} ms billed {billed}")
            if rep.status in (401, 402, 403):
                raise SystemExit(f"stopping {provider}: HTTP {rep.status}")


if __name__ == "__main__":
    provider, phase = sys.argv[1], sys.argv[2]
    try:
        if phase == "decisions":
            run_decisions(provider, sys.argv[3])
        elif phase == "pair":
            run_pair(provider)
        elif phase == "fanout":
            run_fanout(provider)
        else:
            raise SystemExit(f"unknown phase {phase}")
    except CapReached as e:
        log(f"run-{provider}", f"CAP REACHED: {e}")
        raise SystemExit(3)
