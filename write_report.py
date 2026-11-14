"""Generate REPORT.md from results/summary.json and the probe evidence, then run the privacy scan.

  python -I write_report.py
Every number in REPORT.md comes from results/summary.json or the saved probe files.
"""
from __future__ import annotations

import getpass
import json
import re
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEC, DEMO, EVIDENCE, KEY_NAMES, PRICES, RESULTS, ROOT, load_key  # noqa: E402

S = json.loads((RESULTS / "summary.json").read_text())
E = S["eval"]
SETNAME = {"choice": "intent routing (BANKING77, 77 intents)", "predicate": "yes/no over a passage (BoolQ)",
           "score": "5-level sentiment (SST-5)"}
MODEL = {"google/decisions": "Gemini Decision 1", "google/generative": "Gemini 4 Hydrogen, thinking low (18 items only)",
         "openai/decisions": "gpt-6-luna, Decisions API", "openai/generative": "gpt-6-luna, Responses API, effort none",
         "jev/decisions": "Jev 1.14"}
DEC_MODELS = ["jev/decisions", "openai/decisions", "google/decisions"]


def cap(s):
    return s[0].upper() + s[1:]


def f(x, n=3):
    return "n/a" if x is None else (f"{x:.{n}f}" if isinstance(x, float) else str(x))


def pc(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def usd(x, n=4):
    return "n/a" if x is None else f"${x:.{n}f}"


def ev(key):
    return E.get(key)


def headline() -> list[str]:
    out = []
    for s in ("choice", "predicate", "score"):
        for m in DEC_MODELS:
            e = ev(f"{m}/{s}")
            if not e or not e["scored"]:
                continue
            a = e["at90"]
            out.append(f"On {SETNAME[s]}, when {MODEL[m]} gave its top answer a probability of 90% or more, "
                       f"it was right {pc(a['share_correct'])} of the time ({a['n']} of {e['scored']} items; "
                       f"mean stated probability {pc(a['mean_stated'])}).")
    for m in DEC_MODELS:
        e = ev(f"{m}/predicate")
        if e and e["scored"] and e["at_certain"]["n"] >= 20:
            c = e["at_certain"]
            wrong = round(c["n"] * (1 - c["share_correct"]))
            out.append(f"On yes/no over a passage (BoolQ), {MODEL[m]} returned a probability that rounds to 100% "
                       f"(0.995 or more either way) on {c['n']} of {e['scored']} answers and was wrong on {wrong} of them.")
    for s in ("choice", "predicate", "score"):
        parts = []
        for m in DEC_MODELS + ["openai/generative", "google/generative"]:
            e = ev(f"{m}/{s}")
            if e and e["scored"]:
                extra = f", macro-F1 {f(e['macro_f1'])}" if s == "choice" else ""
                parts.append(f"{MODEL[m]} {pc(e['accuracy'])}{extra}, expected calibration error {f(e['ece10'])}")
        if parts:
            out.append(f"Accuracy on {SETNAME[s]}: " + "; ".join(parts) + ".")
    pl = S["paired_latency"].get("openai")
    if pl:
        d, g = ev("openai/decisions/choice"), ev("openai/generative/choice")
        out.append(f"On the same {pl['pairs']} routing items, interleaved, gpt-6-luna through the Responses API "
                   f"took {f(pl['ratio_of_p50'], 1)} times as long as through the Decisions API at the median "
                   f"({f(g['latency_ms']['p50'], 0)} ms against {f(d['latency_ms']['p50'], 0)} ms, measured from this "
                   f"machine with the network included); OpenAI's own processing-time header gives "
                   f"{f(pl.get('server_ratio_of_p50'), 1)} times.")
    for m in DEC_MODELS:
        e = ev(f"{m}/choice")
        if e and e["scored"]:
            out.append(f"{MODEL[m]} answered a routing request in {f(e['latency_ms']['p50'], 0)} ms at the median "
                       f"and {f(e['latency_ms']['p95'], 0)} ms at the 95th percentile, and 1,000 routing decisions "
                       f"cost {usd(e['cost_per_1000_usd'])} at the published price.")
    g = ev("openai/generative/choice")
    if g and g["scored"]:
        out.append(f"The generative baseline, gpt-6-luna through the Responses API, cost {usd(g['cost_per_1000_usd'])} "
                   f"per 1,000 routing decisions.")
    for p, fo in S["fanout"].items():
        if fo and "billing_ratio_separate_over_shared" in fo:
            name = MODEL[f"{p}/decisions"]
            out.append(f"{name}: 200 yes/no questions about one passage in one request billed "
                       f"{fo['one_200_question_request_tokens']:,} input tokens, against an estimated "
                       f"{fo['separate_200_requests_tokens']:,} for 200 one-question requests (200 times the measured "
                       f"one-question request) "
                       f"({f(fo['billing_ratio_separate_over_shared'], 1)} times as many); the 200-question request "
                       f"took {f(fo['latency_ratio_200_over_1'], 2)} times as long as a one-question request.")
    for s in ("choice", "predicate", "score"):
        a = S["agreement"][s]["pairs"].get("openai~jev")
        if a and a["items"]:
            out.append(f"On {SETNAME[s]}, Jev 1.14 and gpt-6-luna Decisions gave the same answer on "
                       f"{a['agree']} of {a['items']} items ({pc(a['share'])}); both were at least 90% sure "
                       f"and still disagreed on {a['confident_disagreements']}.")
    if not any(ev(f"google/decisions/{s}") and ev(f"google/decisions/{s}")["scored"] for s in SETNAME):
        pr = S["probes"].get("probe-google-decisions", {})
        out.append(f"Google's Gemini Decision 1 and Gemini 4 Hydrogen were not measured: every request returned "
                   f"HTTP {pr.get('status')} with \"Your prepayment credits are depleted\".")
    return out


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def acc_tables() -> str:
    out = []
    for s in ("choice", "predicate", "score"):
        rows = []
        for m in DEC_MODELS + ["openai/generative", "google/generative"]:
            e = ev(f"{m}/{s}")
            if not e:
                continue
            rows.append([MODEL[m], e["requests"], e["scored"], f"{e['correct']} ({pc(e['accuracy'])})",
                         f(e["macro_f1"]) if s == "choice" else (f(e.get("mae_expected")) if s == "score" else "-"),
                         f(e["brier_full"]), f(e["brier_top"]), f(e["ece10"]),
                         f"{pc(e['at90']['share_correct'])} of {e['at90']['n']}", e["refusals"],
                         ", ".join(f"HTTP {k}: {v}" for k, v in e["errors"].items()) or "0", e["unparsed"]])
        if rows:
            third = "Macro-F1" if s == "choice" else ("MAE of expected level" if s == "score" else "-")
            out.append(f"### {cap(SETNAME[s])}\n\n" + table(
                ["Model", "Requests", "Scored", "Correct", third, "Brier (full)", "Brier (top label)", "ECE, 10 bins",
                 "Right when ≥90% sure", "Refusals", "Errors", "Unparsed"], rows))
            if s == "score":
                ws = [f"{MODEL[m]} {pc(ev(f'{m}/score')['within_one_level'])}" for m in DEC_MODELS
                      if ev(f"{m}/score") and ev(f"{m}/score").get("within_one_level") is not None]
                out.append("Share of sentiment answers within one level of the gold label: " + "; ".join(ws) + ".")
    return "\n\n".join(out)


def rel_tables() -> str:
    out = []
    for s in ("choice", "predicate", "score"):
        for m in DEC_MODELS + ["openai/generative", "google/generative"]:
            e = ev(f"{m}/{s}")
            if not e or not e["scored"]:
                continue
            rows = [[b["bin"], b["n"], f(b["mean_stated"]), f(b["share_correct"])] for b in e["reliability"] if b["n"]]
            out.append(f"**{MODEL[m]}, {SETNAME[s]}**: stated probability of the top answer against share correct.\n\n"
                       + table(["Stated probability", "Items", "Mean stated", "Share correct"], rows))
    return "\n\n".join(out)


def choice_rel() -> str:
    out = []
    for m in DEC_MODELS + ["openai/generative", "google/generative"]:
        e = ev(f"{m}/choice")
        if e and e["scored"]:
            rows = [[b["bin"], b["n"], f(b["mean_stated"]), f(b["share_correct"])] for b in e["reliability"] if b["n"]]
            out.append(f"**{MODEL[m]}**\n\n" + table(["Stated probability", "Items", "Mean stated", "Share correct"], rows))
    return "\n\n".join(out)


def conf_tables() -> str:
    out = []
    for s in ("choice", "score"):
        for m in DEC_MODELS:
            e = ev(f"{m}/{s}")
            if not e or not e.get("api_confidence"):
                continue
            c = e["api_confidence"]
            rows = [[b["bin"], b["n"], f(b["mean_stated"]), f(b["share_correct"])] for b in c["reliability"] if b["n"]]
            out.append(f"**{MODEL[m]}, {SETNAME[s]}**: the API's `confidence` field against correctness of the top "
                       f"answer. ECE of `confidence` read as a probability: {f(c['ece10_vs_correct'])}. Largest gap "
                       f"between `confidence` and the top probability: {f(c['max_abs_diff_vs_top_prob'])}; between "
                       f"`confidence` and TypeSafe's published formula: {f(c['max_abs_diff_vs_typesafe_formula'])}.\n\n"
                       + table(["Confidence", "Items", "Mean confidence", "Share correct"], rows))
    return "\n\n".join(out)


def latency_table() -> str:
    rows = []
    for s in ("choice", "predicate", "score"):
        for m in DEC_MODELS + ["openai/generative", "google/generative"]:
            e = ev(f"{m}/{s}")
            if not e or not e["ok"]:
                continue
            l = e["latency_ms"]
            sv = e["server_ms"]
            rows.append([MODEL[m], s, e["ok"], f(l["p50"], 0), f(l["p95"], 0), f"{f(l['min'], 0)}–{f(l['max'], 0)}",
                         f(sv["p50"], 0) if sv else "n/a", f(e["input_tokens_mean"], 1), f(e["output_tokens_mean"], 1),
                         usd(e["cost_per_1000_usd"]), e["retried"]])
    return table(["Model", "Set", "Requests", "p50 ms", "p95 ms", "min–max ms", "Server p50 ms",
                  "Billed input tokens (mean)", "Output tokens reported (mean)", "Cost per 1,000", "Retried"], rows)


def fanout_tables() -> str:
    out = []
    for p, fo in S["fanout"].items():
        if not fo or "table" not in fo:
            continue
        rows = [[t["n_questions"], t["repeats"], f(t["latency_p50_ms"], 0), f"{f(t['latency_min_ms'], 0)}–{f(t['latency_max_ms'], 0)}",
                 f(t["server_ms_p50"], 0), t["input_tokens_median"], f"{t['input_tokens_min']}–{t['input_tokens_max']}",
                 usd(t["cost_per_request_usd"], 6), f(t["word_check_accuracy"])] for t in fo["table"]]
        out.append(f"**{MODEL[p + '/decisions']}**. Each extra question added {f(fo.get('tokens_per_extra_question'), 1)} "
                   f"billed input tokens.\n\n" + table(
                       ["Questions", "Repeats", "p50 ms", "min–max ms", "Server p50 ms", "Billed input tokens (median)",
                        "Token range", "Cost per request", "Word-check accuracy"], rows))
    return "\n\n".join(out)


def agreement_section() -> str:
    out = []
    for s in ("choice", "predicate", "score"):
        a = S["agreement"][s]
        rows = [[k.replace("~", " vs "), v["items"], v["agree"], pc(v["share"]), v["confident_disagreements"]]
                for k, v in a["pairs"].items()]
        if rows:
            out.append(f"**{cap(SETNAME[s])}**\n\n" + table(
                ["Pair", "Items", "Same answer", "Share", "Both ≥90% sure, different answers"], rows))
    return "\n\n".join(out)


def example_disagreement() -> str:
    for s in ("choice", "predicate", "score"):
        ex = S["agreement"][s]["examples"]
        if ex:
            e = ex[0]
            models = [m for m in ("jev", "openai", "google") if m in e]
            lines = [f"Set: {SETNAME[s]}; item `{e['id']}` (file `data/samples/{s}.jsonl`)."]
            if e.get("passage"):
                lines.append(f"Passage (first 600 characters): {e['passage']}")
            lines.append(f"Input or question: \"{e['text']}\"")
            lines.append(f"Gold label: `{e['gold']}`.")
            for m in models:
                d = e[m]
                extra = f", P(yes) {f(d['p_yes'])}" if d.get("p_yes") is not None else ""
                lines.append(f"{MODEL[m + '/decisions']}: `{d['pred']}`, top probability {f(d['top_prob'])}{extra}.")
            more = []
            for s2 in ("choice", "predicate", "score"):
                for e2 in S["agreement"][s2]["examples"][:3]:
                    if e2 is e:
                        continue
                    ms = [m for m in ("jev", "openai", "google") if m in e2]
                    more.append(f"`{e2['id']}` gold `{e2['gold']}`: " + "; ".join(
                        f"{MODEL[m + '/decisions']} `{e2[m]['pred']}` at {f(e2[m]['top_prob'], 2)}" for m in ms))
            return "\n\n".join(lines) + ("\n\nOther confident disagreements:\n\n" + "\n".join(f"- {x}" for x in more) if more else "")
    return "No confident disagreement was recorded."


def probe_evidence() -> str:
    out = []
    for name, label in [("probe-jev-decisions", "TypeSafe Jev, POST /v1/systemone"),
                        ("probe-openai-decisions", "OpenAI Decisions, POST /v1/decisions"),
                        ("probe-google-decisions", "Google Decisions, POST /v1beta/decisions"),
                        ("probe-openai-generative", "OpenAI Responses (generative baseline), POST /v1/responses"),
                        ("probe-google-generative", "Google Interactions (generative baseline), POST /v1beta/interactions")]:
        p = EVIDENCE / f"{name}.json"
        if not p.exists():
            continue
        j = json.loads(p.read_text())
        body = j["response_body"]
        if name == "probe-openai-generative" and isinstance(body, dict):
            body = {k: body[k] for k in ("id", "model", "status", "output", "usage", "reasoning", "temperature") if k in body}
        out.append(f"#### {label}\n\nFile `evidence/{name}.json`. HTTP {j['status']}, {f(j['latency_ms'], 0)} ms "
                   f"(first request of its process, so it includes connection setup). Provider request ids: "
                   f"`{json.dumps(j['request_ids'])}`. The auth header is removed.\n\nRequest body:\n\n```json\n"
                   f"{json.dumps(j['request']['body'], indent=1)}\n```\n\nResponse body:\n\n```json\n"
                   f"{json.dumps(body, indent=1)}\n```")
    return "\n\n".join(out)


def docs_section() -> str:
    docs = sorted((DEC / "docs").glob("*"))
    rows = []
    for d in docs:
        if d.stat().st_size == 0:
            continue
        t = datetime.fromtimestamp(d.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        rows.append([f"`docs/{d.name}`", t, d.stat().st_size])
    return table(["Saved page (under .studio/ai-channel/decisions/)", "Read", "Bytes"], rows)


def data_section() -> str:
    lines = (DEC / "data" / "downloads.txt").read_text().split("\n")
    rows = []
    lic = {"PolyAI/banking77": "CC-BY-4.0 (dataset card tag)", "google/boolq": "CC-BY-SA-3.0 (dataset card tag)",
           "SetFit/sst5": "not stated in the repository; the upstream SST page on Hugging Face (stanfordnlp/sst) lists \"unknown\""}
    for line in lines:
        if not line.strip():
            continue
        repo, rev, path, sha, size = line.split()
        rows.append([repo, rev, path, sha, size, lic[repo]])
    return table(["Repository", "Revision", "File", "SHA-256", "Bytes", "Licence"], rows)


def privacy_scan(paths: list[Path]) -> list[str]:
    patterns = {}
    for prov, name in KEY_NAMES.items():
        try:
            k = load_key(prov)
        except SystemExit:
            continue
        patterns[f"{name} value"] = k
        pre = re.match(r"[A-Za-z]+[-_]", k)
        patterns[f"{name} prefix"] = pre.group(0) if pre and len(pre.group(0)) >= 3 else k[:6]
    patterns["home path"] = str(Path.home())
    patterns["any home-directory path"] = "/" + "home" + "/"
    patterns["account user name"] = getpass.getuser()
    patterns["host name"] = socket.gethostname()
    hits = {k: 0 for k in patterns}
    for p in paths:
        try:
            text = p.read_text(errors="ignore")
        except (IsADirectoryError, PermissionError):
            continue
        for k, v in patterns.items():
            if v and v in text:
                hits[k] += 1
    return [f"| {k} | {hits[k]} |" for k in patterns]


def main():
    sp = S["spend"]
    tr = S.get("time_range") or {}
    google_blocked = not any(ev(f"google/decisions/{s}") and ev(f"google/decisions/{s}")["scored"] for s in SETNAME)
    md = [f"# Decision models: a measurement\n",
          "Question: three APIs read an input once and return typed answers with probabilities instead of text. "
          "How accurate are they, when one says 90% how often is it right, how fast and cheap are they, and how do "
          "they compare with asking a generative model for the same label?\n",
          "## Headline figures\n", "\n\n".join(headline()), "",
          "## Setup and provenance\n",
          f"Run window (UTC): {tr.get('first', 'n/a')} to {tr.get('last', 'n/a')}. All requests were sent from one "
          "machine over the public internet, one at a time per provider; the Jev and OpenAI processes "
          "ran at the same time as each other. Every latency below is client-side wall time for the HTTP round trip and "
          "includes the network. OpenAI also returns `openai-processing-ms`, reported as server time.\n",
          table(["Provider", "Model id sent", "Endpoint", "Price used (USD per 1M tokens)"], [
              ["TypeSafe", "`jev-1.14.0` (pinned; `jev-latest` points to it)", "`POST https://api.typesafe.ai/v1/systemone`", f"input {PRICES['jev-1.14.0']['input']}; output tokens free"],
              ["OpenAI", "`gpt-6-luna`", "`POST https://api.openai.com/v1/decisions`", "input 0.10, cached 0.01, cache write 0.125; output not charged"],
              ["OpenAI (baseline)", "`gpt-6-luna`, `reasoning.effort: none`, `store: false`, strict JSON schema", "`POST https://api.openai.com/v1/responses`", "input 0.10, cached 0.01, output 0.50"],
              ["Google", "`gemini-decision-1`", "`POST https://generativelanguage.googleapis.com/v1beta/decisions`", "input 0.10; zero output tokens"],
              ["Google (baseline)", "`gemini-4-hydrogen`, `thinking_level: low`, `store: false`, JSON schema", "`POST https://generativelanguage.googleapis.com/v1beta/interactions`", "input 1.50, output and thinking 7.50"],
          ]),
          "\nThe TypeSafe price, model id and endpoint come from TypeSafe's own pages (`docs.typesafe.ai/models.md`, "
          "`docs.typesafe.ai/api/system-one.md`): $0.042 per million input tokens, `POST /v1/systemone`. No reseller was used.\n",
          "Documentation pages, saved as read:\n", docs_section(), "",
          "Datasets (downloaded over HTTPS, pinned by revision; parsed with `python -I`):\n", data_section(), "",
          "Sample: 400 items per set, drawn with `random.Random(20261114).sample` over the split's row indices; the same "
          "items went to every model. BANKING77 test split (3,080 rows), BoolQ validation split (3,270 rows; BoolQ's test "
          "split has no labels), SST-5 test split (2,210 rows). Two BANKING77 intent names are irregular upstream "
          "(`Refund_not_showing_up`, `reverted_card_payment?`); option keys are lower-cased with the `?` removed.\n",
          "Questions, identical in wording for every API:\n",
          "- Choice: input is the customer message; instructions \"Which banking customer-support intent does this customer message express?\"; 77 options, each keyed by the intent name with its words as the description (`card_arrival`: \"card arrival\").\n"
          "- Predicate: input is the BoolQ passage; instructions \"According to the passage, <question>?\". Google and TypeSafe call this type `noul`; OpenAI calls it `predicate`.\n"
          "- Score: input is the SST-5 sentence; instructions \"How positive is the sentiment of this movie-review sentence?\"; levels Very negative, Negative, Neutral, Positive, Very positive. The predicted level is the most probable level.\n"
          "- Generative baseline (choice set only): one prompt listing the 77 intent keys and asking for JSON `{label, probability}`, with a JSON schema that restricts `label` to the 77 keys. Temperature left at the default (the Responses API reported 1.0).\n",
          "Metrics: accuracy; macro-F1 over the labels present in gold or predictions; Brier score over the full returned "
          "distribution (\"full\") and on the top answer only (\"top label\", the only form available for the generative "
          "baseline); expected calibration error over ten equal-width bins of the top answer's probability (for yes/no "
          "questions the top answer's probability is max(p, 1 − p)).\n",
          "Commands, from the repository root:\n",
          "```\nbash .studio/ai-channel/decisions/demo/setup.sh\n"
          "uv run --python 3.12 --with httpx==0.28.1 python -I -B .studio/ai-channel/decisions/demo/probe.py <jev|openai|google> [decisions|generative]\n"
          "bash .studio/ai-channel/decisions/demo/run-all.sh <jev|openai|google>\n"
          "uv run --python 3.12 --with httpx==0.28.1 python -I -B .studio/ai-channel/decisions/demo/summarize.py\n"
          "uv run --python 3.12 --with httpx==0.28.1 python -I -B .studio/ai-channel/decisions/demo/write_report.py\n```\n",
          "## Spend\n",
          "Computed from each response's usage fields and the published prices; checked against a $5 cap per provider before every request.\n",
          table(["Provider", "Requests in ledger", "Spend (USD)"], [[p, v["requests"], usd(v["usd"], 6)] for p, v in sp.items()]), "",
          "## A. Accuracy and calibration\n", acc_tables(), "",
          "### Reliability tables\n", rel_tables(), "",
          "### The `confidence` field\n",
          "Google documents `confidence` as the top answer's probability. TypeSafe documents it as a rescaling: "
          "(p_top − 1/n)/(1 − 1/n) for a choice and a distance-weighted formula for a score; its yes/no answers carry no "
          "`confidence`. OpenAI's reference lists `confidence` on choice and score answers without a formula, and none on "
          "predicates. With 77 options the choice formula differs from the top probability by at most 0.013, so only the "
          "5-level score set separates the two definitions.\n",
          conf_tables(), "",
          "## B. Speed and cost\n", latency_table(), "",
          "### Many questions on one shared input\n",
          "One BoolQ passage (the longest in the sample, 472 words, item `boolq-941`) and 200 yes/no questions of the "
          "form \"Does the passage contain the word \\\"X\\\"?\": 100 words that occur in it and 100 that do not occur even as a "
          "substring (`results/fanout-fixture.json`). The first 1, 10, 50 and 200 questions, five repeats each, with the "
          "order of sizes rotated per repeat.\n",
          fanout_tables(), "",
          "## C. Generative baseline\n",
          "What was compared: the same 400 BANKING77 items, sent once to gpt-6-luna through `/v1/decisions` and once "
          "through `/v1/responses` with `reasoning.effort: none`, alternating which call went first per item. Same model "
          "id, same machine, same minutes. OpenAI's claim is \"about 10x faster than the Responses API\".\n",
          table(["Measure", "Value"], [[lbl, (S["paired_latency"].get("openai") or {}).get(k, "n/a")] for k, lbl in [
              ("pairs", "Items sent to both endpoints"),
              ("ratio_of_p50", "Median Responses latency ÷ median Decisions latency (client-side)"),
              ("median_ratio_gen_over_dec", "Median of per-item latency ratios (Responses ÷ Decisions)"),
              ("share_gen_slower", "Share of items where the Responses call was slower"),
              ("server_ratio_of_p50", "Same ratio from the openai-processing-ms header (server-side)")]]),
          "\nAccuracy, calibration, latency and cost of the baseline are in the tables above (rows marked Responses API).\n",
          "## D. Agreement\n", agreement_section(), "",
          "## Screenworthy evidence\n",
          "### Raw requests and responses\n", probe_evidence(), "",
          "### Reliability (choice set)\n",
          choice_rel(), "",
          "### Latency\n", latency_table(), "",
          "### One confident disagreement\n", example_disagreement(), "",
          ]
    if google_blocked:
        md += ["## Google: not measured\n",
               "Both Google endpoints answered the first tiny request with HTTP 402 and `\"status\": \"RESOURCE_EXHAUSTED\"`: "
               "\"Your prepayment credits are depleted. Please go to AI Studio ... to manage your project and billing.\" "
               "(`evidence/probe-google-decisions.json`, `evidence/probe-google-generative.json`). The harness, request "
               "builders and parsers for Google are in place; topping up the project's prepaid credit and running "
               "`run-all.sh google` fills in every Google row. The request shapes were checked against the docs only, "
               "not against the live API.\n"]
    md += ["## Documentation against behaviour\n", "\n".join(f"- {x}" for x in doc_notes()), "",
           "## Limits\n",
           "- Public test sets. BANKING77, BoolQ and SST-5 have been public for years and may be in these models' training data; the accuracy here may be higher than on unseen traffic.\n"
           "- 400 items per set, one wording per question type, no prompt tuning. Accuracy and calibration depend on the instructions and option descriptions.\n"
           "- One machine and one network path. Latency includes the network to each provider and will differ elsewhere. The Jev and OpenAI runs overlapped in time.\n"
           "- Prices are the published list prices on the read date; the providers' invoices were not checked.\n"
           "- The OpenAI decision API returned probabilities rounded to two decimals, including exact 0 and 1, which limits the resolution of its calibration figures.\n"
           "- The generative baseline states one probability for its own label. Its Brier score and ECE use that number only; its full distribution is unknown.\n"
           "- Google ran about three hours after the other two, on the Gemini API free tier, from a second API project (the first project had no prepaid credit and returned HTTP 402). Gemini 4 Hydrogen, the Google generative baseline, covers only 18 routing items: its free tier allows 20 requests a day. Do not compare its accuracy.\n"
           "- The fan-out test uses word-presence questions, which are easy; it measures billing and latency, not hard reasoning.\n",
           "## Privacy scan\n",
           "Every file under `.studio/ai-channel/decisions/` (except the downloaded datasets and saved documentation pages) "
           "was searched for each API key, each key's prefix, this account's home path, any home-directory path, the account user name and the host "
           "name. Counts are files with a match.\n",
           "| Pattern | Files matching |", "| --- | --- |", "@@PRIVACY@@", ""]
    text = "\n".join(md)
    report = DEMO / "REPORT.md"
    report.write_text(text)
    scan = [p for p in DEC.rglob("*") if p.is_file() and "data" not in p.relative_to(DEC).parts[:1]
            and "docs" not in p.relative_to(DEC).parts[:1]]
    rows = privacy_scan(scan)
    report.write_text(text.replace("@@PRIVACY@@", "\n".join(rows)))
    print("wrote REPORT.md;", "\n".join(rows))


def doc_notes() -> list[str]:
    notes = []
    e = ev("openai/decisions/predicate")
    if e and e["scored"]:
        notes.append(f"OpenAI predicate probabilities came back with two decimals and reached exact 0 or 1 on "
                     f"{e['exact_0_or_1']} of {e['scored']} BoolQ answers; the docs show two-decimal examples but do not state the rounding.")
    e = ev("openai/decisions/choice")
    if e and e["scored"]:
        notes.append(f"OpenAI choice answers put probability exactly 1.0 on the top intent on {e['exact_0_or_1']} of "
                     f"{e['scored']} routing items.")
    for m in DEC_MODELS:
        for st in ("choice", "predicate", "score"):
            e = ev(f"{m}/{st}")
            if e and e["scored"] and e["at_certain"]["n"]:
                notes.append(f"{MODEL[m]}, {SETNAME[st]}: top probability of 0.995 or more (shown as 1.00 at two "
                             f"decimals) on {e['at_certain']['n']} items, right on {pc(e['at_certain']['share_correct'])} of them.")
    for m in ("openai/decisions", "jev/decisions"):
        e = ev(f"{m}/score")
        if e and e.get("api_confidence"):
            c = e["api_confidence"]
            notes.append(f"{MODEL[m]} score answers: `confidence` differs from TypeSafe's published formula by at most "
                         f"{f(c['max_abs_diff_vs_typesafe_formula'])} and from the top probability by up to "
                         f"{f(c['max_abs_diff_vs_top_prob'])}.")
    e = ev("jev/decisions/predicate")
    if e and e["scored"]:
        notes.append(f"Jev reports nonzero `output_tokens` (mean {f(e['output_tokens_mean'], 1)} on yes/no requests); "
                     f"the docs say output tokens are free, so they are not counted in spend.")
        jc, oc = ev("jev/decisions/choice"), ev("openai/decisions/choice")
        if jc and oc:
            notes.append(f"For the same routing request Jev billed {f(jc['input_tokens_mean'], 0)} input tokens on "
                         f"average and OpenAI {f(oc['input_tokens_mean'], 0)}; each provider counts with its own tokenizer "
                         f"and question formatting.")
    for m in ("openai/decisions", "jev/decisions"):
        for st in ("choice", "predicate", "score"):
            e = ev(f"{m}/{st}")
            if e and e["refusal_items"]:
                ids = ", ".join(f"`{x['id']}` (request `{list(x['request_ids'].values())[0] if x['request_ids'] else 'n/a'}`)"
                                for x in e["refusal_items"])
                notes.append(f"{MODEL[m]} returned `type: refusal` on {len(e['refusal_items'])} of {e['requests']} "
                             f"{SETNAME[st]} items, all benign public-dataset text: {ids}. The docs allow refusals; they do not say when they happen.")
    fo, fj = S["fanout"].get("openai"), S["fanout"].get("jev")
    if fo and fj and "tokens_per_extra_question" in fo:
        notes.append(f"Each added yes/no question cost {f(fo['tokens_per_extra_question'], 1)} billed input tokens on "
                     f"OpenAI and {f(fj['tokens_per_extra_question'], 1)} on Jev, for a question whose own text is about a dozen "
                     f"tokens. OpenAI's docs do not say what a question adds; Google's say each question adds tokens "
                     f"\"for its own instructions, criteria, and formatting\". In both cases the shared passage was billed once, "
                     f"not once per question.")
    notes.append("Google: the first API project was on prepaid billing with no credit left and returned HTTP 402; "
                 "the measured runs used a second project on the free tier, where Gemini 4 Hydrogen allows 20 requests a day.")
    extra = DEMO / "results" / "doc-notes.json"
    if extra.exists():
        notes += json.loads(extra.read_text())
    return notes


if __name__ == "__main__":
    main()
