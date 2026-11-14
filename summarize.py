"""Compute every reported number from results/*.jsonl and write results/summary.json.

  python -I summarize.py
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RESULTS, SAMPLES, banking_labels, option_key  # noqa: E402

PROVIDERS = ["google", "openai", "jev"]
NAMES = {("google", "decisions"): "Gemini Decision 1", ("google", "generative"): "Gemini 4 Hydrogen (low thinking)",
         ("openai", "decisions"): "gpt-6-luna Decisions", ("openai", "generative"): "gpt-6-luna Responses (effort none)",
         ("jev", "decisions"): "Jev 1.14"}
SETS = ["choice", "predicate", "score"]


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def rnd(x, n=4):
    return None if x is None else round(x, n)


def reliability(pairs: list[tuple[float, bool]]) -> list[dict]:
    bins = []
    for b in range(10):
        lo, hi = b / 10, (b + 1) / 10
        sel = [(p, c) for p, c in pairs if (lo <= p < hi) or (b == 9 and p == 1.0)]
        bins.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": len(sel),
                     "mean_stated": rnd(statistics.fmean(p for p, _ in sel)) if sel else None,
                     "share_correct": rnd(sum(c for _, c in sel) / len(sel)) if sel else None})
    return bins


def ece(pairs):
    n = len(pairs)
    if not n:
        return None
    tot = 0.0
    for b in reliability(pairs):
        if b["n"]:
            tot += b["n"] / n * abs(b["mean_stated"] - b["share_correct"])
    return tot


def ece_exact(pairs):
    """ECE without rounding the bin means."""
    n = len(pairs)
    tot = 0.0
    for b in range(10):
        lo, hi = b / 10, (b + 1) / 10
        sel = [(p, c) for p, c in pairs if (lo <= p < hi) or (b == 9 and p == 1.0)]
        if sel:
            tot += len(sel) / n * abs(statistics.fmean(p for p, _ in sel) - sum(c for _, c in sel) / len(sel))
    return tot if n else None


def macro_f1(golds, preds):
    labels = sorted(set(golds) | set(preds))
    f1s = []
    for lab in labels:
        tp = sum(1 for g, p in zip(golds, preds) if g == lab and p == lab)
        fp = sum(1 for g, p in zip(golds, preds) if g != lab and p == lab)
        fn = sum(1 for g, p in zip(golds, preds) if g == lab and p != lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return statistics.fmean(f1s)


def gold_key(task, gold):
    if task == "choice":
        return option_key(gold)
    return gold


def evaluate(rows: list[dict], task: str, api: str, n_options: int) -> dict:
    ok = [r for r in rows if r["status"] == 200]
    errors = Counter(str(r["status"]) for r in rows if r["status"] != 200)
    refusals = [r for r in ok if r["answer"].get("refusal")]
    unparsed = [r for r in ok if api == "generative" and not r["answer"].get("refusal") and not r["answer"].get("parse_ok")]
    usable = [r for r in ok if not r["answer"].get("refusal") and (api != "generative" or r["answer"].get("parse_ok"))]
    golds, preds, top_pairs, brier_full, brier_top = [], [], [], [], []
    conf_pairs, conf_check, sums, abs_err, within1 = [], [], [], [], []
    exact_01 = 0
    for r in usable:
        a = r["answer"]
        g = gold_key(task, r["gold"])
        if task == "predicate":
            p = a["p_yes"]
            pred = p >= 0.5
            ptop = max(p, 1 - p)
            brier_full.append((p - (1.0 if g else 0.0)) ** 2)
            exact_01 += p in (0.0, 1.0)
        elif api == "generative":
            pred, ptop = a["pred"], a["stated_p"]
        else:
            probs = a["probs"]
            pred = a["pred"]
            ptop = max(probs.values())
            sums.append(sum(probs.values()))
            exact_01 += ptop == 1.0
            if task == "score":
                pred = int(pred)
                keys = [str(i) for i in range(n_options)]
                brier_full.append(sum((probs.get(k, 0.0) - (1.0 if int(k) == g else 0.0)) ** 2 for k in keys))
                ev = sum(int(k) * v for k, v in probs.items())
                abs_err.append(abs(ev - g))
                within1.append(abs(pred - g) <= 1)
            else:
                brier_full.append(sum((v - (1.0 if k == g else 0.0)) ** 2 for k, v in probs.items())
                                  + (0.0 if g in probs else 1.0))
            if a.get("api_confidence") is not None:
                conf = float(a["api_confidence"])
                k = n_options
                if task == "score":
                    lv = [probs.get(str(i), 0.0) for i in range(k)]
                    m = max(range(k), key=lambda i: lv[i])
                    mad = sum(abs(i - (k - 1) / 2) for i in range(k)) / k
                    formula = max(0.0, 1 - sum(lv[i] * abs(i - m) for i in range(k)) / mad)
                else:
                    formula = (ptop - 1 / k) / (1 - 1 / k)
                conf_check.append({"conf": conf, "ptop": ptop, "norm": formula})
        correct = pred == g
        golds.append(g)
        preds.append(pred)
        top_pairs.append((ptop, correct))
        brier_top.append((ptop - (1.0 if correct else 0.0)) ** 2)
        if a.get("api_confidence") is not None:
            conf_pairs.append((float(a["api_confidence"]), correct))
    lat = [r["latency_ms"] for r in ok]
    server = [float(r["request_ids"]["openai-processing-ms"]) for r in ok if "openai-processing-ms" in r.get("request_ids", {})]
    tin = [r["billed"].get("input", 0) for r in ok]
    tout = [r["billed"].get("output", 0) + r["billed"].get("thought", 0) + r["billed"].get("output_free", 0) for r in ok]
    costs = [r["cost_usd"] for r in ok]
    hi = [(p, c) for p, c in top_pairs if p >= 0.9]
    certain = [(p, c) for p, c in top_pairs if p >= 0.995]
    out = {
        "requests": len(rows), "ok": len(ok), "errors": dict(errors), "refusals": len(refusals),
        "unparsed": len(unparsed), "scored": len(usable),
        "refusal_items": [{"id": r["id"], "request_ids": r["request_ids"]} for r in refusals],
        "accuracy": rnd(sum(1 for g, p in zip(golds, preds) if g == p) / len(golds)) if golds else None,
        "correct": sum(1 for g, p in zip(golds, preds) if g == p),
        "macro_f1": rnd(macro_f1(golds, preds)) if task == "choice" and golds else None,
        "brier_full": rnd(statistics.fmean(brier_full)) if brier_full else None,
        "brier_top": rnd(statistics.fmean(brier_top)) if brier_top else None,
        "ece10": rnd(ece_exact(top_pairs)) if top_pairs else None,
        "reliability": reliability(top_pairs),
        "at90": {"n": len(hi), "share_correct": rnd(sum(c for _, c in hi) / len(hi)) if hi else None,
                 "mean_stated": rnd(statistics.fmean(p for p, _ in hi)) if hi else None},
        "at_certain": {"n": len(certain), "share_correct": rnd(sum(c for _, c in certain) / len(certain)) if certain else None},
        "mean_top_prob": rnd(statistics.fmean(p for p, _ in top_pairs)) if top_pairs else None,
        "exact_0_or_1": exact_01,
        "api_confidence": None,
        "latency_ms": {"p50": rnd(pct(lat, .5), 1), "p95": rnd(pct(lat, .95), 1), "min": rnd(min(lat), 1) if lat else None,
                       "max": rnd(max(lat), 1) if lat else None},
        "server_ms": {"p50": rnd(pct(server, .5), 1), "p95": rnd(pct(server, .95), 1), "n": len(server)} if server else None,
        "input_tokens_mean": rnd(statistics.fmean(tin), 1) if tin else None,
        "output_tokens_mean": rnd(statistics.fmean(tout), 1) if tout else None,
        "cost_total_usd": rnd(sum(costs), 6),
        "cost_per_1000_usd": rnd(1000 * statistics.fmean(costs), 5) if costs else None,
        "retried": sum(1 for r in rows if r.get("attempts", 1) > 1),
    }
    if task == "score" and abs_err:
        out["mae_expected"] = rnd(statistics.fmean(abs_err))
        out["within_one_level"] = rnd(sum(within1) / len(within1))
    if sums:
        out["prob_sum"] = {"min": rnd(min(sums)), "max": rnd(max(sums))}
    if conf_pairs:
        out["api_confidence"] = {
            "n": len(conf_pairs),
            "reliability": reliability(conf_pairs),
            "ece10_vs_correct": rnd(ece_exact(conf_pairs)),
            "max_abs_diff_vs_top_prob": rnd(max(abs(c["conf"] - c["ptop"]) for c in conf_check), 4) if conf_check else None,
            "max_abs_diff_vs_typesafe_formula": rnd(max(abs(c["conf"] - c["norm"]) for c in conf_check), 4) if conf_check else None,
        }
    return out


def paired_latency(dec: list[dict], gen: list[dict]) -> dict | None:
    d = {r["id"]: r for r in dec if r["status"] == 200}
    g = {r["id"]: r for r in gen if r["status"] == 200}
    ids = sorted(set(d) & set(g))
    if not ids:
        return None
    ratios = [g[i]["latency_ms"] / d[i]["latency_ms"] for i in ids]
    out = {"pairs": len(ids), "median_ratio_gen_over_dec": rnd(statistics.median(ratios), 3),
           "ratio_of_p50": rnd(statistics.median(g[i]["latency_ms"] for i in ids) / statistics.median(d[i]["latency_ms"] for i in ids), 3),
           "share_gen_slower": rnd(sum(1 for x in ratios if x > 1) / len(ratios), 4)}
    ds = [float(d[i]["request_ids"]["openai-processing-ms"]) for i in ids if "openai-processing-ms" in d[i]["request_ids"]]
    gs = [float(g[i]["request_ids"]["openai-processing-ms"]) for i in ids if "openai-processing-ms" in g[i]["request_ids"]]
    if ds and gs:
        out["server_ratio_of_p50"] = rnd(statistics.median(gs) / statistics.median(ds), 3)
    return out


def agreement(results: dict, task: str, items: dict) -> dict:
    models = [p for p in PROVIDERS if results.get((p, "decisions", task))]
    per = {}
    for p in models:
        per[p] = {}
        for r in results[(p, "decisions", task)]:
            if r["status"] != 200 or r["answer"].get("refusal"):
                continue
            a = r["answer"]
            if task == "predicate":
                per[p][r["id"]] = (a["p_yes"] >= 0.5, max(a["p_yes"], 1 - a["p_yes"]), a["p_yes"])
            else:
                pred = int(a["pred"]) if task == "score" else a["pred"]
                per[p][r["id"]] = (pred, max(a["probs"].values()), None)
    pairs = {}
    examples = []
    for i, p in enumerate(models):
        for q in models[i + 1:]:
            ids = sorted(set(per[p]) & set(per[q]))
            same = sum(1 for k in ids if per[p][k][0] == per[q][k][0])
            conf_dis = [k for k in ids if per[p][k][0] != per[q][k][0] and per[p][k][1] >= 0.9 and per[q][k][1] >= 0.9]
            pairs[f"{p}~{q}"] = {"items": len(ids), "agree": same, "share": rnd(same / len(ids)) if ids else None,
                                 "confident_disagreements": len(conf_dis)}
            for k in conf_dis:
                it = items[k]
                examples.append({
                    "id": k, "pair": f"{p}~{q}", "gold": it["gold"],
                    "text": it.get("text") or it.get("question"),
                    "passage": (it.get("passage") or "")[:600] or None,
                    p: {"pred": per[p][k][0], "top_prob": per[p][k][1], "p_yes": per[p][k][2]},
                    q: {"pred": per[q][k][0], "top_prob": per[q][k][1], "p_yes": per[q][k][2]},
                })
    allm = None
    if len(models) >= 2:
        ids = set.intersection(*(set(per[p]) for p in models))
        allm = {"models": models, "items": len(ids),
                "all_agree": sum(1 for k in ids if len({per[p][k][0] for p in models}) == 1)}
    examples.sort(key=lambda e: -min(e[m]["top_prob"] for m in e if m in per))
    return {"pairs": pairs, "all": allm, "examples": examples[:12]}


def fanout(rows: list[dict]) -> dict | None:
    ok = [r for r in rows if r["status"] == 200]
    if not ok:
        return {"errors": Counter(str(r["status"]) for r in rows)} if rows else None
    by = defaultdict(list)
    for r in ok:
        by[r["n_questions"]].append(r)
    table = []
    for k in sorted(by):
        rs = by[k]
        lat = [r["latency_ms"] for r in rs]
        tin = [r["billed"].get("input", 0) for r in rs]
        cor = [a["p_yes"] is not None and ((a["p_yes"] >= 0.5) == a["gold"]) for r in rs for a in r.get("answers", []) if not a["refusal"]]
        table.append({"n_questions": k, "repeats": len(rs), "latency_p50_ms": rnd(pct(lat, .5), 1),
                      "latency_min_ms": rnd(min(lat), 1), "latency_max_ms": rnd(max(lat), 1),
                      "input_tokens_median": statistics.median(tin), "input_tokens_min": min(tin), "input_tokens_max": max(tin),
                      "cost_per_request_usd": rnd(statistics.fmean(r["cost_usd"] for r in rs), 8),
                      "word_check_accuracy": rnd(sum(cor) / len(cor)) if cor else None,
                      "server_ms_p50": rnd(pct([float(r["request_ids"]["openai-processing-ms"]) for r in rs
                                                if "openai-processing-ms" in r["request_ids"]], .5), 1)})
    t = {x["n_questions"]: x for x in table}
    out = {"table": table}
    if 1 in t and 200 in t:
        t1, t200 = t[1]["input_tokens_median"], t[200]["input_tokens_median"]
        out["tokens_per_extra_question"] = rnd((t200 - t1) / 199, 2)
        out["separate_200_requests_tokens"] = 200 * t1
        out["one_200_question_request_tokens"] = t200
        out["billing_ratio_separate_over_shared"] = rnd(200 * t1 / t200, 3)
        out["latency_ratio_200_over_1"] = rnd(t[200]["latency_p50_ms"] / t[1]["latency_p50_ms"], 3)
    return out


def main():
    labels = banking_labels()
    results = {}
    for p in PROVIDERS:
        for api in ("decisions", "generative"):
            for s in SETS + ["fanout"]:
                rows = load(RESULTS / f"{p}-{api}-{s}.jsonl")
                if rows:
                    results[(p, api, s)] = rows
    items = {}
    for s in SETS:
        for line in (SAMPLES / f"{s}.jsonl").read_text().splitlines():
            r = json.loads(line)
            items[r["id"]] = r
    nopt = {"choice": len(labels), "predicate": 2, "score": 5}
    summary = {"models": {f"{p}/{a}": NAMES[(p, a)] for (p, a) in NAMES}, "eval": {}, "paired_latency": {},
               "agreement": {}, "fanout": {}, "spend": {}, "probes": {}, "time_range": {}}
    for (p, api, s), rows in results.items():
        if s == "fanout":
            summary["fanout"][p] = fanout(rows)
        else:
            summary["eval"][f"{p}/{api}/{s}"] = evaluate(rows, s, api, nopt[s])
    for p in PROVIDERS:
        dec, gen = results.get((p, "decisions", "choice")), results.get((p, "generative", "choice"))
        if dec and gen:
            summary["paired_latency"][p] = paired_latency(dec, gen)
    for s in SETS:
        summary["agreement"][s] = agreement(results, s, items)
    for p in PROVIDERS:
        led = load(RESULTS / f"ledger-{p}.jsonl")
        summary["spend"][p] = {"requests": len(led), "usd": rnd(sum(x["cost_usd"] for x in led), 6)}
    times = [r["t"] for rows in results.values() for r in rows]
    if times:
        summary["time_range"] = {"first": min(times), "last": max(times)}
    for f in sorted((RESULTS.parent / "evidence").glob("probe-*.json")):
        j = json.loads(f.read_text())
        summary["probes"][f.stem] = {"status": j["status"], "latency_ms": rnd(j["latency_ms"], 1), "t": j["t"],
                                     "error": (j["response_body"] if j["status"] != 200 else None)}
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print("wrote results/summary.json")


if __name__ == "__main__":
    main()
