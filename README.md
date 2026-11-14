# Decision models: when they say 90%, how often are they right?

A measurement by [Vikawork](https://vikawork.com/), 14 November 2026. Three APIs read an input once and return a
typed answer with probabilities instead of text: TypeSafe's Jev 1.14 (`/v1/systemone`), OpenAI's gpt-6-luna through
the Decisions API, and Google's Gemini Decision 1. We sent each the same 400 items from three public test sets and
checked accuracy, calibration, speed and cost, and compared them with asking a generative model for the same label.

| Set | Model | Correct | Right when ≥90% sure | Calibration error (ECE) |
| --- | --- | ---: | ---: | ---: |
| Intent routing (BANKING77, 77 intents) | Jev 1.14 | 81.0% | 94.3% of 263 | 0.068 |
| | gpt-6-luna, Decisions API | 77.9% | 88.5% of 262 | 0.093 |
| | Gemini Decision 1 | 81.2% | 96.4% of 223 | 0.033 |
| | gpt-6-luna, Responses API (generative baseline) | 81.5% | 88.2% of 289 | 0.092 |
| Yes/no over a passage (BoolQ) | Jev 1.14 | 89.0% | 96.5% of 289 | 0.021 |
| | gpt-6-luna, Decisions API | 86.6% | 92.9% of 336 | 0.084 |
| | Gemini Decision 1 | 86.5% | 96.0% of 296 | 0.040 |
| 5-level sentiment (SST-5) | Jev 1.14 | 56.5% | 67.4% of 95 | 0.184 |
| | gpt-6-luna, Decisions API | 53.8% | 60.7% of 112 | 0.236 |
| | Gemini Decision 1 | 55.0% | never ≥90% sure | 0.037 |

- On BoolQ, gpt-6-luna's Decisions API returned a probability that rounds to 100% on 287 of 396 answers and was
  wrong on 17 of them. Its probabilities come back with two decimals.
- On the same 400 routing items, interleaved, gpt-6-luna took 10.0 times as long through the Responses API as
  through the Decisions API at the median (1,188 ms against 118 ms, client-side, network included).
- Median routing latency: gpt-6-luna Decisions 118 ms, Jev 262 ms, Gemini Decision 1 637 ms. Cost per 1,000
  routing decisions at list prices: $0.0708, $0.0985 and $0.1099 (Jev, OpenAI, Google).
- 200 yes/no questions about one passage in one request: each extra question added 17.2 billed input tokens on Jev,
  48.6 on Gemini Decision 1 and 153.9 on gpt-6-luna.

The whole run cost $0.29 across the three providers. Limits: public test sets that may be in the models' training
data; one wording per question; one machine and one network path; Google ran about three hours after the others on
the free tier; Gemini 4 Hydrogen, the Google generative baseline, covers only 18 items.

[REPORT.md](REPORT.md) has every table, the reliability bins, raw requests and responses, the documentation checks
and the limits. It is written by `write_report.py` from `results/summary.json`, which `summarize.py` builds from
`results/*.jsonl`.

## What is here

- `common.py`, `run.py`, `run-all.sh`, `probe.py`, `summarize.py`, `write_report.py`: the harness. API keys are read
  from a `.env` file at run time and redacted from everything written to disk.
- `setup.sh`, `make_samples.py`: the original download and sampling step. `fetch_sst5.py`: see below.
- `results/`: one JSONL row per request (item id, gold label, the API's answer and probabilities, latency, usage,
  billed cost, request ids), per-provider spend ledgers, the fan-out fixture and `summary.json`.
- `evidence/`: full redacted request and response bodies from the first probe of each API.
- `logs/`: run logs.
- `data/samples/`: the BANKING77 and BoolQ samples we sent, `score-ids.jsonl` (SST-5 item ids and gold labels, no
  text) and `meta.json`. `data/downloads.txt` lists the dataset files with their SHA-256.

Not included: the SST-5 sentences, the full dataset downloads, and the provider documentation pages the report lists
as saved (they are the providers' copyright; the report gives each URL-derived name, read time and size).

## SST-5 text is fetched, not included

The SST-5 copy we used, [SetFit/sst5](https://huggingface.co/datasets/SetFit/sst5), states no licence, so its
sentences are not in this repository. The result files hold only item ids, gold labels and model outputs. To get the
inputs back:

```sh
python3 -I fetch_sst5.py
```

It downloads `test.jsonl` at revision `e51bdcd8cd3a30da231967c1a249ba59361279a3`, checks SHA-256
`1384216112a34f3d70b6fa210762f3399bb080410c0456ac6e54a5cb413f04b2`, draws the same 400 items with seed 20261114,
checks them against `data/samples/score-ids.jsonl` and writes `data/samples/score.jsonl` (git-ignored).

## Run it

Needs [uv](https://docs.astral.sh/uv/), Python 3.12 and keys in `.env` as `JEV_API_KEY`, `OPENAI_API_KEY` and
`GEMINI_API_KEY`. The scripts were written inside a larger repository: they expect this folder as `demo/` inside a
`decisions/` folder that holds `data/`, three levels below the folder with `.env`. Change `ROOT` and `DEC` at the top
of `common.py` (and `D` in the shell scripts) to run them elsewhere. The commands, run from the folder that holds
`.env`, are listed under "Commands" in [REPORT.md](REPORT.md): `setup.sh` (downloads and samples all three datasets),
`probe.py`, `run-all.sh <jev|openai|google>`, `summarize.py`, `write_report.py`.

These are paid APIs. `run.py` checks a $5 cap per provider before every request; our full run spent $0.29.

## Licence and credits

Our code is under the MIT licence ([LICENSE](LICENSE)); the report and results may be reused with credit to
Vikawork, subject to the dataset terms below.

- **BANKING77**: PolyAI, [PolyAI/banking77](https://huggingface.co/datasets/PolyAI/banking77) at revision
  `1846984189f2bc0ac51c6fc3a600fa9e1714e0c6`, licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  Casanueva et al., [Efficient Intent Detection with Dual Sentence Encoders](https://arxiv.org/abs/2003.04807)
  (2020). Used in `data/samples/choice.jsonl` (400 test-split messages, unchanged) and the intent labels.
- **BoolQ**: Google, [google/boolq](https://huggingface.co/datasets/google/boolq) at revision
  `35b264d03638db9f4ce671b711558bf7ff0f80d5`, licensed
  [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Clark et al.,
  [BoolQ: Exploring the Surprising Difficulty of Natural Yes/No Questions](https://arxiv.org/abs/1905.10044)
  (NAACL 2019). Used in `data/samples/predicate.jsonl` (400 validation-split items, unchanged),
  `results/fanout-fixture.json` (one passage, item `boolq-941`, with our own word-presence questions) and the
  passages quoted in `REPORT.md` and `results/summary.json`. **Share-alike:** that BoolQ material is under
  CC BY-SA 3.0, and anything you adapt from it must be shared under the same licence.
- **SST-5**: Socher et al., Stanford Sentiment Treebank, via [SetFit/sst5](https://huggingface.co/datasets/SetFit/sst5).
  Not redistributed; see above.

[SCAN.md](SCAN.md) records the privacy scan run before publishing.
