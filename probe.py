"""One tiny request per API to check the documented request and response shapes before any measured run.

Usage: python -I probe.py <provider> [generative]
Saves the scrubbed request, response headers and body to evidence/probe-<provider>-<api>.json.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder; add only our own code
from common import (EVIDENCE, ENDPOINTS, Http, Ledger, Q, build_decision, build_generative, cost_of,
                    decision_usage, generative_usage, log, now, parse_decision, parse_generative, scrub)

TEXT = "The blue mug I ordered on Monday arrived cracked on Wednesday."
QS = [
    Q("is_damaged", "predicate", "Did the item arrive damaged?"),
    Q("queue", "choice", "Which support queue should handle this message?",
      ["billing", "replacements", "general"],
      ["Payment, invoice, or refund questions.", "Damaged, missing, or wrong items.", "Product questions and account updates."]),
    Q("urgency", "score", "How urgent is this message?", ["Can wait", "Needs attention this week", "Needs attention today"]),
]
LABELS = ["billing", "replacements", "general"]


def main(provider: str, api: str) -> None:
    led = Ledger(provider)
    led.check(0.01)
    http = Http(provider)
    url = ENDPOINTS[(provider, api)]
    if api == "decisions":
        payload = build_decision(provider, TEXT, QS)
    else:
        payload = build_generative(provider, TEXT, LABELS)
    rep = http.post(url, payload, f"probe-{provider}")
    usage_key, usage = (decision_usage if api == "decisions" else generative_usage)(provider, rep.body)
    cost, billed = cost_of(usage_key, usage) if rep.status == 200 else (0.0, {})
    led.add(cost, f"probe-{api}")
    parsed = None
    if rep.status == 200:
        parsed = parse_decision(provider, rep.body, QS) if api == "decisions" else parse_generative(provider, rep.body, LABELS)
    rec = {
        "t": now(), "provider": provider, "api": api, "url": url,
        "request": {"method": "POST", "headers": {"Content-Type": "application/json", "auth": "[REDACTED]"}, "body": payload},
        "status": rep.status, "latency_ms": rep.latency_ms, "request_ids": rep.request_ids,
        "response_headers": rep.headers, "response_body": rep.body if rep.body is not None else rep.text[:4000],
        "billed": billed, "cost_usd": cost, "parsed": parsed,
    }
    (EVIDENCE / f"probe-{provider}-{api}.json").write_text(json.dumps(scrub(rec), indent=1))
    log(f"probe-{provider}", f"{api} status={rep.status} latency_ms={rep.latency_ms:.0f} billed={billed} cost={cost:.8f}")
    print(json.dumps(scrub({"status": rep.status, "body": rep.body if rep.body is not None else rep.text[:2000], "parsed": parsed}), indent=1)[:6000])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "decisions")
