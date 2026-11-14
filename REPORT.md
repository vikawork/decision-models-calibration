# Decision models: a measurement

Question: three APIs read an input once and return typed answers with probabilities instead of text. How accurate are they, when one says 90% how often is it right, how fast and cheap are they, and how do they compare with asking a generative model for the same label?

## Headline figures

On intent routing (BANKING77, 77 intents), when Jev 1.14 gave its top answer a probability of 90% or more, it was right 94.3% of the time (263 of 400 items; mean stated probability 98.2%).

On intent routing (BANKING77, 77 intents), when gpt-6-luna, Decisions API gave its top answer a probability of 90% or more, it was right 88.5% of the time (262 of 398 items; mean stated probability 97.8%).

On intent routing (BANKING77, 77 intents), when Gemini Decision 1 gave its top answer a probability of 90% or more, it was right 96.4% of the time (223 of 400 items; mean stated probability 97.0%).

On yes/no over a passage (BoolQ), when Jev 1.14 gave its top answer a probability of 90% or more, it was right 96.5% of the time (289 of 400 items; mean stated probability 96.1%).

On yes/no over a passage (BoolQ), when gpt-6-luna, Decisions API gave its top answer a probability of 90% or more, it was right 92.9% of the time (336 of 396 items; mean stated probability 99.5%).

On yes/no over a passage (BoolQ), when Gemini Decision 1 gave its top answer a probability of 90% or more, it was right 96.0% of the time (296 of 400 items; mean stated probability 96.9%).

On 5-level sentiment (SST-5), when Jev 1.14 gave its top answer a probability of 90% or more, it was right 67.4% of the time (95 of 400 items; mean stated probability 95.1%).

On 5-level sentiment (SST-5), when gpt-6-luna, Decisions API gave its top answer a probability of 90% or more, it was right 60.7% of the time (112 of 400 items; mean stated probability 94.8%).

On 5-level sentiment (SST-5), when Gemini Decision 1 gave its top answer a probability of 90% or more, it was right n/a of the time (0 of 400 items; mean stated probability n/a).

On yes/no over a passage (BoolQ), gpt-6-luna, Decisions API returned a probability that rounds to 100% (0.995 or more either way) on 287 of 396 answers and was wrong on 17 of them.

Accuracy on intent routing (BANKING77, 77 intents): Jev 1.14 81.0%, macro-F1 0.808, expected calibration error 0.068; gpt-6-luna, Decisions API 77.9%, macro-F1 0.766, expected calibration error 0.093; Gemini Decision 1 81.2%, macro-F1 0.806, expected calibration error 0.033; gpt-6-luna, Responses API, effort none 81.5%, macro-F1 0.813, expected calibration error 0.092; Gemini 4 Hydrogen, thinking low (18 items only) 83.3%, macro-F1 0.704, expected calibration error 0.133.

Accuracy on yes/no over a passage (BoolQ): Jev 1.14 89.0%, expected calibration error 0.021; gpt-6-luna, Decisions API 86.6%, expected calibration error 0.084; Gemini Decision 1 86.5%, expected calibration error 0.040.

Accuracy on 5-level sentiment (SST-5): Jev 1.14 56.5%, expected calibration error 0.184; gpt-6-luna, Decisions API 53.8%, expected calibration error 0.236; Gemini Decision 1 55.0%, expected calibration error 0.037.

On the same 400 routing items, interleaved, gpt-6-luna through the Responses API took 10.0 times as long as through the Decisions API at the median (1188 ms against 118 ms, measured from this machine with the network included); OpenAI's own processing-time header gives 13.6 times.

Jev 1.14 answered a routing request in 262 ms at the median and 304 ms at the 95th percentile, and 1,000 routing decisions cost $0.0708 at the published price.

gpt-6-luna, Decisions API answered a routing request in 118 ms at the median and 280 ms at the 95th percentile, and 1,000 routing decisions cost $0.0985 at the published price.

Gemini Decision 1 answered a routing request in 637 ms at the median and 857 ms at the 95th percentile, and 1,000 routing decisions cost $0.1099 at the published price.

The generative baseline, gpt-6-luna through the Responses API, cost $0.1085 per 1,000 routing decisions.

Gemini Decision 1: 200 yes/no questions about one passage in one request billed 10,319 input tokens, against an estimated 129,000 for 200 one-question requests (200 times the measured one-question request) (12.5 times as many); the 200-question request took 2.13 times as long as a one-question request.

gpt-6-luna, Decisions API: 200 yes/no questions about one passage in one request billed 31,331 input tokens, against an estimated 142,000 for 200 one-question requests (200 times the measured one-question request) (4.5 times as many); the 200-question request took 2.57 times as long as a one-question request.

Jev 1.14: 200 yes/no questions about one passage in one request billed 4,253 input tokens, against an estimated 167,200 for 200 one-question requests (200 times the measured one-question request) (39.3 times as many); the 200-question request took 1.21 times as long as a one-question request.

On intent routing (BANKING77, 77 intents), Jev 1.14 and gpt-6-luna Decisions gave the same answer on 352 of 398 items (88.4%); both were at least 90% sure and still disagreed on 0.

On yes/no over a passage (BoolQ), Jev 1.14 and gpt-6-luna Decisions gave the same answer on 362 of 396 items (91.4%); both were at least 90% sure and still disagreed on 1.

On 5-level sentiment (SST-5), Jev 1.14 and gpt-6-luna Decisions gave the same answer on 299 of 400 items (74.8%); both were at least 90% sure and still disagreed on 0.

## Setup and provenance

Run window (UTC): 2026-11-14T14:26:16.074129Z to 2026-11-14T17:52:09.166783Z. All requests were sent from one machine over the public internet, one at a time per provider; the Jev and OpenAI processes ran at the same time as each other. Every latency below is client-side wall time for the HTTP round trip and includes the network. OpenAI also returns `openai-processing-ms`, reported as server time.

| Provider | Model id sent | Endpoint | Price used (USD per 1M tokens) |
| --- | --- | --- | --- |
| TypeSafe | `jev-1.14.0` (pinned; `jev-latest` points to it) | `POST https://api.typesafe.ai/v1/systemone` | input 0.042; output tokens free |
| OpenAI | `gpt-6-luna` | `POST https://api.openai.com/v1/decisions` | input 0.10, cached 0.01, cache write 0.125; output not charged |
| OpenAI (baseline) | `gpt-6-luna`, `reasoning.effort: none`, `store: false`, strict JSON schema | `POST https://api.openai.com/v1/responses` | input 0.10, cached 0.01, output 0.50 |
| Google | `gemini-decision-1` | `POST https://generativelanguage.googleapis.com/v1beta/decisions` | input 0.10; zero output tokens |
| Google (baseline) | `gemini-4-hydrogen`, `thinking_level: low`, `store: false`, JSON schema | `POST https://generativelanguage.googleapis.com/v1beta/interactions` | input 1.50, output and thinking 7.50 |

The TypeSafe price, model id and endpoint come from TypeSafe's own pages (`docs.typesafe.ai/models.md`, `docs.typesafe.ai/api/system-one.md`): $0.042 per million input tokens, `POST /v1/systemone`. No reseller was used.

Documentation pages, saved as read:

| Saved page (under .studio/ai-channel/decisions/) | Read | Bytes |
| --- | --- | --- |
| `docs/aistudio.google.com_docs_decisions-api.md.txt` | 2026-11-14 14:19 UTC | 46477 |
| `docs/aistudio.google.com_docs_interactions-overview.md.txt` | 2026-11-14 14:20 UTC | 19210 |
| `docs/aistudio.google.com_docs_models.md.txt` | 2026-11-14 14:20 UTC | 24274 |
| `docs/aistudio.google.com_docs_models_gemini-4-hydrogen.md.txt` | 2026-11-14 14:20 UTC | 4883 |
| `docs/aistudio.google.com_docs_models_gemini-decision-1` | 2026-11-14 14:19 UTC | 44495 |
| `docs/aistudio.google.com_docs_models_gemini-decision-1.md.txt` | 2026-11-14 14:19 UTC | 8832 |
| `docs/aistudio.google.com_docs_pricing` | 2026-11-14 14:19 UTC | 149078 |
| `docs/aistudio.google.com_docs_pricing.md.txt` | 2026-11-14 14:19 UTC | 111627 |
| `docs/aistudio.google.com_docs_rate-limits.md.txt` | 2026-11-14 14:19 UTC | 11666 |
| `docs/aistudio.google.com_docs_structured-output.md.txt` | 2026-11-14 14:20 UTC | 61423 |
| `docs/aistudio.google.com_docs_thinking.md.txt` | 2026-11-14 14:20 UTC | 38986 |
| `docs/developers.openai.com_api_docs_guides_decisions` | 2026-11-14 14:19 UTC | 656389 |
| `docs/developers.openai.com_api_docs_guides_decisions.md` | 2026-11-14 14:19 UTC | 38194 |
| `docs/developers.openai.com_api_docs_guides_reasoning.md` | 2026-11-14 14:21 UTC | 70357 |
| `docs/developers.openai.com_api_docs_models_gpt-6-luna.md` | 2026-11-14 14:21 UTC | 4370 |
| `docs/developers.openai.com_api_docs_pricing.md` | 2026-11-14 14:19 UTC | 21230 |
| `docs/developers.openai.com_api_reference_resources_decisions` | 2026-11-14 14:19 UTC | 669234 |
| `docs/developers.openai.com_api_reference_resources_decisions.md` | 2026-11-14 14:19 UTC | 36338 |
| `docs/developers.openai.com_api_reference_resources_decisions_methods_create.md` | 2026-11-14 14:19 UTC | 22782 |
| `docs/docs.typesafe.ai_` | 2026-11-14 14:19 UTC | 170804 |
| `docs/docs.typesafe.ai_llms.txt` | 2026-11-14 14:19 UTC | 21897 |
| `docs/typesafe_api_errors.md` | 2026-11-14 14:20 UTC | 2722 |
| `docs/typesafe_api_list-models.md` | 2026-11-14 14:20 UTC | 6026 |
| `docs/typesafe_api_system-one.md` | 2026-11-14 14:20 UTC | 29761 |
| `docs/typesafe_changelog.md` | 2026-11-14 14:20 UTC | 1220 |
| `docs/typesafe_confidence.md` | 2026-11-14 14:20 UTC | 14159 |
| `docs/typesafe_introduction_quickstart.md` | 2026-11-14 14:20 UTC | 15156 |
| `docs/typesafe_model-jaggedness.md` | 2026-11-14 14:20 UTC | 9536 |
| `docs/typesafe_models.md` | 2026-11-14 14:20 UTC | 8177 |
| `docs/typesafe_openapi.json` | 2026-11-14 14:20 UTC | 22467 |
| `docs/typesafe_primitives.md` | 2026-11-14 14:20 UTC | 16368 |
| `docs/typesafe_primitives_choice.md` | 2026-11-14 14:20 UTC | 15647 |
| `docs/typesafe_primitives_noul.md` | 2026-11-14 14:20 UTC | 16697 |
| `docs/typesafe_primitives_score.md` | 2026-11-14 14:20 UTC | 20657 |

Datasets (downloaded over HTTPS, pinned by revision; parsed with `python -I`):

| Repository | Revision | File | SHA-256 | Bytes | Licence |
| --- | --- | --- | --- | --- | --- |
| PolyAI/banking77 | 1846984189f2bc0ac51c6fc3a600fa9e1714e0c6 | data/test-00000-of-00001.parquet | 1f40f777c33f0edfa6c530ff84fe2878db6490838c12d22d036f626948905341 | 92409 | CC-BY-4.0 (dataset card tag) |
| PolyAI/banking77 | 1846984189f2bc0ac51c6fc3a600fa9e1714e0c6 | README.md | f3786a5327fd6533c7c0ff3ff654e20ee3d1261d2fa41667381f59a2e42364e1 | 13049 | CC-BY-4.0 (dataset card tag) |
| google/boolq | 35b264d03638db9f4ce671b711558bf7ff0f80d5 | data/validation-00000-of-00001.parquet | 52355d11524b4b874a9b9dcc278feb10f672d52c4f4eff9872e695ede59820f8 | 1257630 | CC-BY-SA-3.0 (dataset card tag) |
| google/boolq | 35b264d03638db9f4ce671b711558bf7ff0f80d5 | README.md | 07447668f46c7c1e62e24b650ea2a73f1ab34f2b3759b1587c7b7a81b4bf1cf4 | 6570 | CC-BY-SA-3.0 (dataset card tag) |
| SetFit/sst5 | e51bdcd8cd3a30da231967c1a249ba59361279a3 | test.jsonl | 1384216112a34f3d70b6fa210762f3399bb080410c0456ac6e54a5cb413f04b2 | 342783 | not stated in the repository; the upstream SST page on Hugging Face (stanfordnlp/sst) lists "unknown" |
| SetFit/sst5 | e51bdcd8cd3a30da231967c1a249ba59361279a3 | README.md | 8fb6d394783212981c77f3642084d1f1e938bc9f19cce8576e44a8aa29b5bbe8 | 421 | not stated in the repository; the upstream SST page on Hugging Face (stanfordnlp/sst) lists "unknown" |

Sample: 400 items per set, drawn with `random.Random(20261114).sample` over the split's row indices; the same items went to every model. BANKING77 test split (3,080 rows), BoolQ validation split (3,270 rows; BoolQ's test split has no labels), SST-5 test split (2,210 rows). Two BANKING77 intent names are irregular upstream (`Refund_not_showing_up`, `reverted_card_payment?`); option keys are lower-cased with the `?` removed.

Questions, identical in wording for every API:

- Choice: input is the customer message; instructions "Which banking customer-support intent does this customer message express?"; 77 options, each keyed by the intent name with its words as the description (`card_arrival`: "card arrival").
- Predicate: input is the BoolQ passage; instructions "According to the passage, <question>?". Google and TypeSafe call this type `noul`; OpenAI calls it `predicate`.
- Score: input is the SST-5 sentence; instructions "How positive is the sentiment of this movie-review sentence?"; levels Very negative, Negative, Neutral, Positive, Very positive. The predicted level is the most probable level.
- Generative baseline (choice set only): one prompt listing the 77 intent keys and asking for JSON `{label, probability}`, with a JSON schema that restricts `label` to the 77 keys. Temperature left at the default (the Responses API reported 1.0).

Metrics: accuracy; macro-F1 over the labels present in gold or predictions; Brier score over the full returned distribution ("full") and on the top answer only ("top label", the only form available for the generative baseline); expected calibration error over ten equal-width bins of the top answer's probability (for yes/no questions the top answer's probability is max(p, 1 − p)).

Commands, from the repository root:

```
bash .studio/ai-channel/decisions/demo/setup.sh
uv run --python 3.12 --with httpx==0.28.1 python -I -B .studio/ai-channel/decisions/demo/probe.py <jev|openai|google> [decisions|generative]
bash .studio/ai-channel/decisions/demo/run-all.sh <jev|openai|google>
uv run --python 3.12 --with httpx==0.28.1 python -I -B .studio/ai-channel/decisions/demo/summarize.py
uv run --python 3.12 --with httpx==0.28.1 python -I -B .studio/ai-channel/decisions/demo/write_report.py
```

## Spend

Computed from each response's usage fields and the published prices; checked against a $5 cap per provider before every request.

| Provider | Requests in ledger | Spend (USD) |
| --- | --- | --- |
| google | 1254 | $0.125634 |
| openai | 1622 | $0.121372 |
| jev | 1221 | $0.042582 |

## A. Accuracy and calibration

### Intent routing (BANKING77, 77 intents)

| Model | Requests | Scored | Correct | Macro-F1 | Brier (full) | Brier (top label) | ECE, 10 bins | Right when ≥90% sure | Refusals | Errors | Unparsed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jev 1.14 | 400 | 400 | 324 (81.0%) | 0.808 | 0.297 | 0.120 | 0.068 | 94.3% of 263 | 0 | 0 | 0 |
| gpt-6-luna, Decisions API | 400 | 398 | 310 (77.9%) | 0.766 | 0.344 | 0.144 | 0.093 | 88.5% of 262 | 2 | 0 | 0 |
| Gemini Decision 1 | 400 | 400 | 325 (81.2%) | 0.806 | 0.276 | 0.108 | 0.033 | 96.4% of 223 | 0 | 0 | 0 |
| gpt-6-luna, Responses API, effort none | 400 | 400 | 326 (81.5%) | 0.813 | n/a | 0.139 | 0.092 | 88.2% of 289 | 0 | 0 | 0 |
| Gemini 4 Hydrogen, thinking low (18 items only) | 18 | 18 | 15 (83.3%) | 0.704 | n/a | 0.146 | 0.133 | 88.2% of 17 | 0 | 0 | 0 |

### Yes/no over a passage (BoolQ)

| Model | Requests | Scored | Correct | - | Brier (full) | Brier (top label) | ECE, 10 bins | Right when ≥90% sure | Refusals | Errors | Unparsed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jev 1.14 | 400 | 400 | 356 (89.0%) | - | 0.080 | 0.080 | 0.021 | 96.5% of 289 | 0 | 0 | 0 |
| gpt-6-luna, Decisions API | 400 | 396 | 343 (86.6%) | - | 0.102 | 0.102 | 0.084 | 92.9% of 336 | 4 | 0 | 0 |
| Gemini Decision 1 | 400 | 400 | 346 (86.5%) | - | 0.088 | 0.088 | 0.040 | 96.0% of 296 | 0 | 0 | 0 |

### 5-level sentiment (SST-5)

| Model | Requests | Scored | Correct | MAE of expected level | Brier (full) | Brier (top label) | ECE, 10 bins | Right when ≥90% sure | Refusals | Errors | Unparsed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jev 1.14 | 400 | 400 | 226 (56.5%) | 0.502 | 0.621 | 0.275 | 0.184 | 67.4% of 95 | 0 | 0 | 0 |
| gpt-6-luna, Decisions API | 400 | 400 | 215 (53.8%) | 0.527 | 0.686 | 0.305 | 0.236 | 60.7% of 112 | 0 | 0 | 0 |
| Gemini Decision 1 | 400 | 400 | 220 (55.0%) | 0.497 | 0.559 | 0.244 | 0.037 | n/a of 0 | 0 | 0 | 0 |

Share of sentiment answers within one level of the gold label: Jev 1.14 95.8%; gpt-6-luna, Decisions API 96.0%; Gemini Decision 1 98.5%.

### Reliability tables

**Jev 1.14, intent routing (BANKING77, 77 intents)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.2-0.3 | 1 | 0.250 | 0.000 |
| 0.3-0.4 | 3 | 0.347 | 0.000 |
| 0.4-0.5 | 15 | 0.456 | 0.400 |
| 0.5-0.6 | 22 | 0.543 | 0.455 |
| 0.6-0.7 | 28 | 0.652 | 0.571 |
| 0.7-0.8 | 28 | 0.738 | 0.643 |
| 0.8-0.9 | 40 | 0.845 | 0.650 |
| 0.9-1.0 | 263 | 0.982 | 0.943 |

**gpt-6-luna, Decisions API, intent routing (BANKING77, 77 intents)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.1-0.2 | 2 | 0.155 | 0.000 |
| 0.2-0.3 | 10 | 0.272 | 0.400 |
| 0.3-0.4 | 10 | 0.336 | 0.400 |
| 0.4-0.5 | 16 | 0.443 | 0.250 |
| 0.5-0.6 | 19 | 0.539 | 0.579 |
| 0.6-0.7 | 17 | 0.650 | 0.588 |
| 0.7-0.8 | 22 | 0.748 | 0.682 |
| 0.8-0.9 | 40 | 0.851 | 0.750 |
| 0.9-1.0 | 262 | 0.978 | 0.885 |

**Gemini Decision 1, intent routing (BANKING77, 77 intents)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.2-0.3 | 4 | 0.258 | 0.000 |
| 0.3-0.4 | 8 | 0.362 | 0.500 |
| 0.4-0.5 | 22 | 0.458 | 0.273 |
| 0.5-0.6 | 27 | 0.550 | 0.481 |
| 0.6-0.7 | 31 | 0.662 | 0.677 |
| 0.7-0.8 | 28 | 0.746 | 0.679 |
| 0.8-0.9 | 57 | 0.852 | 0.825 |
| 0.9-1.0 | 223 | 0.970 | 0.964 |

**gpt-6-luna, Responses API, effort none, intent routing (BANKING77, 77 intents)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.1-0.2 | 1 | 0.170 | 0.000 |
| 0.3-0.4 | 2 | 0.370 | 0.500 |
| 0.4-0.5 | 6 | 0.433 | 0.333 |
| 0.5-0.6 | 11 | 0.558 | 0.364 |
| 0.6-0.7 | 15 | 0.645 | 0.600 |
| 0.7-0.8 | 24 | 0.751 | 0.750 |
| 0.8-0.9 | 52 | 0.857 | 0.712 |
| 0.9-1.0 | 289 | 0.970 | 0.882 |

**Gemini 4 Hydrogen, thinking low (18 items only), intent routing (BANKING77, 77 intents)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.8-0.9 | 1 | 0.850 | 0.000 |
| 0.9-1.0 | 17 | 0.974 | 0.882 |

**Jev 1.14, yes/no over a passage (BoolQ)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.5-0.6 | 16 | 0.541 | 0.500 |
| 0.6-0.7 | 22 | 0.647 | 0.682 |
| 0.7-0.8 | 25 | 0.747 | 0.600 |
| 0.8-0.9 | 48 | 0.851 | 0.812 |
| 0.9-1.0 | 289 | 0.961 | 0.965 |

**gpt-6-luna, Decisions API, yes/no over a passage (BoolQ)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.5-0.6 | 16 | 0.536 | 0.500 |
| 0.6-0.7 | 11 | 0.626 | 0.273 |
| 0.7-0.8 | 13 | 0.738 | 0.615 |
| 0.8-0.9 | 20 | 0.854 | 0.600 |
| 0.9-1.0 | 336 | 0.995 | 0.929 |

**Gemini Decision 1, yes/no over a passage (BoolQ)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.5-0.6 | 14 | 0.553 | 0.214 |
| 0.6-0.7 | 34 | 0.652 | 0.529 |
| 0.7-0.8 | 19 | 0.750 | 0.684 |
| 0.8-0.9 | 37 | 0.846 | 0.757 |
| 0.9-1.0 | 296 | 0.969 | 0.960 |

**Jev 1.14, 5-level sentiment (SST-5)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.3-0.4 | 10 | 0.364 | 0.400 |
| 0.4-0.5 | 18 | 0.457 | 0.500 |
| 0.5-0.6 | 60 | 0.553 | 0.400 |
| 0.6-0.7 | 79 | 0.649 | 0.532 |
| 0.7-0.8 | 59 | 0.745 | 0.559 |
| 0.8-0.9 | 79 | 0.846 | 0.633 |
| 0.9-1.0 | 95 | 0.951 | 0.674 |

**gpt-6-luna, Decisions API, 5-level sentiment (SST-5)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.3-0.4 | 5 | 0.346 | 0.600 |
| 0.4-0.5 | 14 | 0.455 | 0.214 |
| 0.5-0.6 | 53 | 0.542 | 0.472 |
| 0.6-0.7 | 60 | 0.643 | 0.450 |
| 0.7-0.8 | 69 | 0.748 | 0.551 |
| 0.8-0.9 | 87 | 0.847 | 0.586 |
| 0.9-1.0 | 112 | 0.948 | 0.607 |

**Gemini Decision 1, 5-level sentiment (SST-5)**: stated probability of the top answer against share correct.

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.3-0.4 | 15 | 0.376 | 0.333 |
| 0.4-0.5 | 100 | 0.463 | 0.510 |
| 0.5-0.6 | 198 | 0.551 | 0.561 |
| 0.6-0.7 | 64 | 0.633 | 0.578 |
| 0.7-0.8 | 16 | 0.741 | 0.562 |
| 0.8-0.9 | 7 | 0.855 | 1.000 |

### The `confidence` field

Google documents `confidence` as the top answer's probability. TypeSafe documents it as a rescaling: (p_top − 1/n)/(1 − 1/n) for a choice and a distance-weighted formula for a score; its yes/no answers carry no `confidence`. OpenAI's reference lists `confidence` on choice and score answers without a formula, and none on predicates. With 77 options the choice formula differs from the top probability by at most 0.013, so only the 5-level score set separates the two definitions.

**Jev 1.14, intent routing (BANKING77, 77 intents)**: the API's `confidence` field against correctness of the top answer. ECE of `confidence` read as a probability: 0.067. Largest gap between `confidence` and the top probability: 0.010; between `confidence` and TypeSafe's published formula: 0.005.

| Confidence | Items | Mean confidence | Share correct |
| --- | --- | --- | --- |
| 0.2-0.3 | 1 | 0.240 | 0.000 |
| 0.3-0.4 | 3 | 0.337 | 0.000 |
| 0.4-0.5 | 17 | 0.451 | 0.412 |
| 0.5-0.6 | 21 | 0.539 | 0.476 |
| 0.6-0.7 | 27 | 0.653 | 0.556 |
| 0.7-0.8 | 28 | 0.738 | 0.643 |
| 0.8-0.9 | 40 | 0.845 | 0.650 |
| 0.9-1.0 | 263 | 0.982 | 0.943 |

**gpt-6-luna, Decisions API, intent routing (BANKING77, 77 intents)**: the API's `confidence` field against correctness of the top answer. ECE of `confidence` read as a probability: 0.089. Largest gap between `confidence` and the top probability: 0.010; between `confidence` and TypeSafe's published formula: 0.005.

| Confidence | Items | Mean confidence | Share correct |
| --- | --- | --- | --- |
| 0.1-0.2 | 3 | 0.160 | 0.333 |
| 0.2-0.3 | 11 | 0.274 | 0.364 |
| 0.3-0.4 | 9 | 0.341 | 0.333 |
| 0.4-0.5 | 18 | 0.445 | 0.333 |
| 0.5-0.6 | 17 | 0.539 | 0.588 |
| 0.6-0.7 | 16 | 0.652 | 0.562 |
| 0.7-0.8 | 22 | 0.748 | 0.682 |
| 0.8-0.9 | 40 | 0.851 | 0.750 |
| 0.9-1.0 | 262 | 0.978 | 0.885 |

**Gemini Decision 1, intent routing (BANKING77, 77 intents)**: the API's `confidence` field against correctness of the top answer. ECE of `confidence` read as a probability: 0.033. Largest gap between `confidence` and the top probability: 0.000; between `confidence` and TypeSafe's published formula: 0.010.

| Confidence | Items | Mean confidence | Share correct |
| --- | --- | --- | --- |
| 0.2-0.3 | 4 | 0.258 | 0.000 |
| 0.3-0.4 | 8 | 0.362 | 0.500 |
| 0.4-0.5 | 22 | 0.458 | 0.273 |
| 0.5-0.6 | 27 | 0.550 | 0.481 |
| 0.6-0.7 | 31 | 0.662 | 0.677 |
| 0.7-0.8 | 28 | 0.746 | 0.679 |
| 0.8-0.9 | 57 | 0.852 | 0.825 |
| 0.9-1.0 | 223 | 0.970 | 0.964 |

**Jev 1.14, 5-level sentiment (SST-5)**: the API's `confidence` field against correctness of the top answer. ECE of `confidence` read as a probability: 0.215. Largest gap between `confidence` and the top probability: 0.360; between `confidence` and TypeSafe's published formula: 0.005.

| Confidence | Items | Mean confidence | Share correct |
| --- | --- | --- | --- |
| 0.0-0.1 | 5 | 0.022 | 0.600 |
| 0.1-0.2 | 4 | 0.155 | 0.500 |
| 0.2-0.3 | 2 | 0.220 | 0.500 |
| 0.3-0.4 | 3 | 0.350 | 0.000 |
| 0.4-0.5 | 18 | 0.450 | 0.278 |
| 0.5-0.6 | 33 | 0.561 | 0.455 |
| 0.6-0.7 | 67 | 0.646 | 0.507 |
| 0.7-0.8 | 76 | 0.739 | 0.553 |
| 0.8-0.9 | 84 | 0.849 | 0.631 |
| 0.9-1.0 | 108 | 0.952 | 0.657 |

**gpt-6-luna, Decisions API, 5-level sentiment (SST-5)**: the API's `confidence` field against correctness of the top answer. ECE of `confidence` read as a probability: 0.252. Largest gap between `confidence` and the top probability: 0.290; between `confidence` and TypeSafe's published formula: 0.005.

| Confidence | Items | Mean confidence | Share correct |
| --- | --- | --- | --- |
| 0.0-0.1 | 1 | 0.070 | 1.000 |
| 0.1-0.2 | 4 | 0.168 | 0.500 |
| 0.2-0.3 | 3 | 0.247 | 0.000 |
| 0.3-0.4 | 6 | 0.327 | 0.167 |
| 0.4-0.5 | 11 | 0.455 | 0.273 |
| 0.5-0.6 | 30 | 0.558 | 0.433 |
| 0.6-0.7 | 57 | 0.649 | 0.474 |
| 0.7-0.8 | 76 | 0.750 | 0.566 |
| 0.8-0.9 | 89 | 0.850 | 0.551 |
| 0.9-1.0 | 123 | 0.948 | 0.618 |

**Gemini Decision 1, 5-level sentiment (SST-5)**: the API's `confidence` field against correctness of the top answer. ECE of `confidence` read as a probability: 0.037. Largest gap between `confidence` and the top probability: 0.000; between `confidence` and TypeSafe's published formula: 0.167.

| Confidence | Items | Mean confidence | Share correct |
| --- | --- | --- | --- |
| 0.3-0.4 | 15 | 0.376 | 0.333 |
| 0.4-0.5 | 100 | 0.463 | 0.510 |
| 0.5-0.6 | 198 | 0.551 | 0.561 |
| 0.6-0.7 | 64 | 0.633 | 0.578 |
| 0.7-0.8 | 16 | 0.741 | 0.562 |
| 0.8-0.9 | 7 | 0.855 | 1.000 |

## B. Speed and cost

| Model | Set | Requests | p50 ms | p95 ms | min–max ms | Server p50 ms | Billed input tokens (mean) | Output tokens reported (mean) | Cost per 1,000 | Retried |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jev 1.14 | choice | 400 | 262 | 304 | 236–545 | n/a | 1685.8 | 826.3 | $0.0708 | 0 |
| gpt-6-luna, Decisions API | choice | 400 | 118 | 280 | 99–1097 | 66 | 984.6 | 0.0 | $0.0985 | 0 |
| Gemini Decision 1 | choice | 400 | 637 | 857 | 240–3565 | n/a | 1099.0 | 0.0 | $0.1099 | 6 |
| gpt-6-luna, Responses API, effort none | choice | 400 | 1188 | 1890 | 860–4276 | 903 | 974.5 | 22.1 | $0.1085 | 0 |
| Gemini 4 Hydrogen, thinking low (18 items only) | choice | 18 | 15175 | 34248 | 2763–56579 | n/a | 1485.6 | 122.4 | $3.1467 | 3 |
| Jev 1.14 | predicate | 400 | 253 | 307 | 225–850 | n/a | 412.7 | 21.0 | $0.0173 | 0 |
| gpt-6-luna, Decisions API | predicate | 400 | 123 | 257 | 95–651 | 72 | 285.1 | 0.0 | $0.0285 | 0 |
| Gemini Decision 1 | predicate | 400 | 475 | 644 | 193–1084 | n/a | 224.0 | 0.0 | $0.0224 | 1 |
| Jev 1.14 | score | 400 | 252 | 331 | 226–724 | n/a | 338.2 | 18.0 | $0.0142 | 0 |
| gpt-6-luna, Decisions API | score | 400 | 116 | 252 | 93–281 | 66 | 148.2 | 0.0 | $0.0148 | 0 |
| Gemini Decision 1 | score | 400 | 453 | 529 | 177–1111 | n/a | 135.3 | 0.0 | $0.0135 | 0 |

### Many questions on one shared input

One BoolQ passage (the longest in the sample, 472 words, item `boolq-941`) and 200 yes/no questions of the form "Does the passage contain the word \"X\"?": 100 words that occur in it and 100 that do not occur even as a substring (`results/fanout-fixture.json`). The first 1, 10, 50 and 200 questions, five repeats each, with the order of sizes rotated per repeat.

**Gemini Decision 1**. Each extra question added 48.6 billed input tokens.

| Questions | Repeats | p50 ms | min–max ms | Server p50 ms | Billed input tokens (median) | Token range | Cost per request | Word-check accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5 | 478 | 395–767 | n/a | 645 | 645–645 | $0.000064 | 1.000 |
| 10 | 5 | 745 | 362–1066 | n/a | 1082 | 1082–1082 | $0.000108 | 1.000 |
| 50 | 5 | 751 | 289–822 | n/a | 3023 | 3023–3023 | $0.000302 | 1.000 |
| 200 | 5 | 1019 | 930–1111 | n/a | 10319 | 10319–10319 | $0.001032 | 0.995 |

**gpt-6-luna, Decisions API**. Each extra question added 153.9 billed input tokens.

| Questions | Repeats | p50 ms | min–max ms | Server p50 ms | Billed input tokens (median) | Token range | Cost per request | Word-check accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5 | 108 | 101–274 | 63 | 710 | 710–710 | $0.000071 | 1.000 |
| 10 | 5 | 150 | 126–272 | 106 | 2094 | 2094–2094 | $0.000209 | 1.000 |
| 50 | 5 | 236 | 177–525 | 185 | 8247 | 8247–8247 | $0.000825 | 0.940 |
| 200 | 5 | 278 | 267–574 | 227 | 31331 | 31331–31331 | $0.003133 | 0.950 |

**Jev 1.14**. Each extra question added 17.2 billed input tokens.

| Questions | Repeats | p50 ms | min–max ms | Server p50 ms | Billed input tokens (median) | Token range | Cost per request | Word-check accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5 | 246 | 244–298 | n/a | 836 | 836–836 | $0.000035 | 1.000 |
| 10 | 5 | 268 | 237–348 | n/a | 988 | 988–988 | $0.000041 | 1.000 |
| 50 | 5 | 266 | 252–282 | n/a | 1673 | 1673–1673 | $0.000070 | 0.940 |
| 200 | 5 | 297 | 284–341 | n/a | 4253 | 4253–4253 | $0.000179 | 0.986 |

## C. Generative baseline

What was compared: the same 400 BANKING77 items, sent once to gpt-6-luna through `/v1/decisions` and once through `/v1/responses` with `reasoning.effort: none`, alternating which call went first per item. Same model id, same machine, same minutes. OpenAI's claim is "about 10x faster than the Responses API".

| Measure | Value |
| --- | --- |
| Items sent to both endpoints | 400 |
| Median Responses latency ÷ median Decisions latency (client-side) | 10.03 |
| Median of per-item latency ratios (Responses ÷ Decisions) | 9.935 |
| Share of items where the Responses call was slower | 1.0 |
| Same ratio from the openai-processing-ms header (server-side) | 13.579 |

Accuracy, calibration, latency and cost of the baseline are in the tables above (rows marked Responses API).

## D. Agreement

**Intent routing (BANKING77, 77 intents)**

| Pair | Items | Same answer | Share | Both ≥90% sure, different answers |
| --- | --- | --- | --- | --- |
| google vs openai | 398 | 355 | 89.2% | 0 |
| google vs jev | 400 | 368 | 92.0% | 0 |
| openai vs jev | 398 | 352 | 88.4% | 0 |

**Yes/no over a passage (BoolQ)**

| Pair | Items | Same answer | Share | Both ≥90% sure, different answers |
| --- | --- | --- | --- | --- |
| google vs openai | 396 | 364 | 91.9% | 1 |
| google vs jev | 400 | 372 | 93.0% | 0 |
| openai vs jev | 396 | 362 | 91.4% | 1 |

**5-level sentiment (SST-5)**

| Pair | Items | Same answer | Share | Both ≥90% sure, different answers |
| --- | --- | --- | --- | --- |
| google vs openai | 400 | 307 | 76.8% | 0 |
| google vs jev | 400 | 306 | 76.5% | 0 |
| openai vs jev | 400 | 299 | 74.8% | 0 |

## Screenworthy evidence

### Raw requests and responses

#### TypeSafe Jev, POST /v1/systemone

File `evidence/probe-jev-decisions.json`. HTTP 200, 299 ms (first request of its process, so it includes connection setup). Provider request ids: `{"x-typesafe-request-id": "req_01a1da72a43474abb6fc18c30f1a3858"}`. The auth header is removed.

Request body:

```json
{
 "model": "jev-1.14.0",
 "state": "The blue mug I ordered on Monday arrived cracked on Wednesday.",
 "questions": {
  "is_damaged": {
   "type": "noul",
   "instructions": "Did the item arrive damaged?"
  },
  "queue": {
   "type": "choice",
   "instructions": "Which support queue should handle this message?",
   "criteria": {
    "billing": "Payment, invoice, or refund questions.",
    "replacements": "Damaged, missing, or wrong items.",
    "general": "Product questions and account updates."
   }
  },
  "urgency": {
   "type": "score",
   "instructions": "How urgent is this message?",
   "criteria": [
    "Can wait",
    "Needs attention this week",
    "Needs attention today"
   ]
  }
 }
}
```

Response body:

```json
{
 "model": "jev-1.14.0",
 "answers": {
  "is_damaged": {
   "type": "noul",
   "noul": 0.98
  },
  "queue": {
   "type": "choice",
   "choice": "replacements",
   "confidence": 1.0,
   "probabilities": {
    "billing": 0.0,
    "replacements": 1.0,
    "general": 0.0
   }
  },
  "urgency": {
   "type": "score",
   "score": 1.09,
   "confidence": 0.6,
   "legend": {
    "0": "Can wait",
    "1": "Needs attention this week",
    "2": "Needs attention today"
   },
   "probabilities": {
    "0": 0.09,
    "1": 0.73,
    "2": 0.18
   }
  }
 },
 "usage": {
  "input_tokens": 410,
  "output_tokens": 76
 }
}
```

#### OpenAI Decisions, POST /v1/decisions

File `evidence/probe-openai-decisions.json`. HTTP 200, 3867 ms (first request of its process, so it includes connection setup). Provider request ids: `{"x-request-id": "req_76e46845ad664f9cae38c39e8dace2f4"}`. The auth header is removed.

Request body:

```json
{
 "model": "gpt-6-luna",
 "input": "The blue mug I ordered on Monday arrived cracked on Wednesday.",
 "questions": [
  {
   "type": "predicate",
   "name": "is_damaged",
   "instructions": "Did the item arrive damaged?"
  },
  {
   "type": "choice",
   "name": "queue",
   "instructions": "Which support queue should handle this message?",
   "choices": [
    {
     "value": "billing",
     "description": "Payment, invoice, or refund questions."
    },
    {
     "value": "replacements",
     "description": "Damaged, missing, or wrong items."
    },
    {
     "value": "general",
     "description": "Product questions and account updates."
    }
   ]
  },
  {
   "type": "score",
   "name": "urgency",
   "instructions": "How urgent is this message?",
   "levels": [
    {
     "label": "Can wait"
    },
    {
     "label": "Needs attention this week"
    },
    {
     "label": "Needs attention today"
    }
   ]
  }
 ]
}
```

Response body:

```json
{
 "model": "gpt-6-luna",
 "answers": [
  {
   "type": "predicate",
   "name": "is_damaged",
   "probability": 1.0
  },
  {
   "type": "choice",
   "name": "queue",
   "choice": "replacements",
   "probabilities": [
    {
     "value": "billing",
     "probability": 0.0
    },
    {
     "value": "replacements",
     "probability": 1.0
    },
    {
     "value": "general",
     "probability": 0.0
    }
   ],
   "confidence": 1.0
  },
  {
   "type": "score",
   "name": "urgency",
   "score": 1.59,
   "probabilities": [
    {
     "value": 0,
     "label": "Can wait",
     "probability": 0.02
    },
    {
     "value": 1,
     "label": "Needs attention this week",
     "probability": 0.37
    },
    {
     "value": 2,
     "label": "Needs attention today",
     "probability": 0.61
    }
   ],
   "confidence": 0.39
  }
 ],
 "usage": {
  "input_tokens": 411,
  "input_tokens_details": {
   "cached_tokens": 0,
   "cache_write_tokens": 0
  },
  "output_tokens": 0,
  "output_tokens_details": {
   "reasoning_tokens": 0
  },
  "total_tokens": 411
 }
}
```

#### Google Decisions, POST /v1beta/decisions

File `evidence/probe-google-decisions.json`. HTTP 200, 580 ms (first request of its process, so it includes connection setup). Provider request ids: `{"server-timing": "gfet4t7; dur=499"}`. The auth header is removed.

Request body:

```json
{
 "model": "gemini-decision-1",
 "input": "The blue mug I ordered on Monday arrived cracked on Wednesday.",
 "questions": {
  "is_damaged": {
   "type": "noul",
   "instructions": "Did the item arrive damaged?"
  },
  "queue": {
   "type": "choice",
   "instructions": "Which support queue should handle this message?",
   "criteria": {
    "billing": "Payment, invoice, or refund questions.",
    "replacements": "Damaged, missing, or wrong items.",
    "general": "Product questions and account updates."
   }
  },
  "urgency": {
   "type": "score",
   "instructions": "How urgent is this message?",
   "criteria": [
    "Can wait",
    "Needs attention this week",
    "Needs attention today"
   ]
  }
 }
}
```

Response body:

```json
{
 "answers": {
  "queue": {
   "confidence": 0.9838489287002516,
   "choice": "replacements",
   "probabilities": {
    "general": 0.006358368440704238,
    "billing": 0.009792702859044131,
    "replacements": 0.9838489287002516
   },
   "type": "choice"
  },
  "is_damaged": {
   "confidence": 0.99,
   "noul": 0.99,
   "type": "noul"
  },
  "urgency": {
   "confidence": 0.5148230336255861,
   "score": 0.9448677482878949,
   "probabilities": {
    "0": 0.27015460904325944,
    "1": 0.5148230336255861,
    "2": 0.21502235733115435
   },
   "legend": {
    "1": "Needs attention this week",
    "2": "Needs attention today",
    "0": "Can wait"
   },
   "type": "score"
  }
 },
 "usage": {
  "total_tokens": 233,
  "total_input_tokens": 233,
  "input_tokens_by_modality": [
   {
    "modality": "text",
    "tokens": 233
   }
  ],
  "total_output_tokens": 0
 }
}
```

#### OpenAI Responses (generative baseline), POST /v1/responses

File `evidence/probe-openai-generative.json`. HTTP 200, 4076 ms (first request of its process, so it includes connection setup). Provider request ids: `{"x-request-id": "req_c76d30a70b5c4b42bc1c85b0df36380d", "openai-processing-ms": "1748"}`. The auth header is removed.

Request body:

```json
{
 "model": "gpt-6-luna",
 "input": "Classify the customer message into exactly one banking customer-support intent from the list.\nReturn JSON with two fields: \"label\" (one intent from the list, copied exactly) and \"probability\" (your probability, from 0 to 1, that the label is correct).\n\nIntents:\n- billing\n- replacements\n- general\n\nCustomer message:\nThe blue mug I ordered on Monday arrived cracked on Wednesday.",
 "reasoning": {
  "effort": "none"
 },
 "store": false,
 "max_output_tokens": 400,
 "text": {
  "format": {
   "type": "json_schema",
   "name": "intent",
   "strict": true,
   "schema": {
    "type": "object",
    "properties": {
     "label": {
      "type": "string",
      "enum": [
       "billing",
       "replacements",
       "general"
      ]
     },
     "probability": {
      "type": "number"
     }
    },
    "required": [
     "label",
     "probability"
    ],
    "additionalProperties": false
   }
  }
 }
}
```

Response body:

```json
{
 "id": "resp_08bf037e8d70a31f016af86f4276c487d29e948914c81c6506",
 "model": "gpt-6-luna",
 "status": "completed",
 "output": [
  {
   "id": "msg_08bf037e8d70a31f016af86f43da7887d2bf4b4c3b58e719d8",
   "type": "message",
   "status": "completed",
   "content": [
    {
     "type": "output_text",
     "annotations": [],
     "logprobs": [],
     "text": "{\"label\":\"replacements\",\"probability\":0.98}"
    }
   ],
   "phase": "final_answer",
   "role": "assistant"
  }
 ],
 "usage": {
  "input_tokens": 128,
  "input_tokens_details": {
   "cache_write_tokens": 0,
   "cache_write_tokens_details": {
    "ttl_12h_tokens": 0,
    "ttl_30m_tokens": 0
   },
   "cached_tokens": 0
  },
  "output_tokens": 20,
  "output_tokens_details": {
   "reasoning_tokens": 0
  },
  "total_tokens": 148
 },
 "reasoning": {
  "context": "all_turns",
  "effort": "none",
  "mode": "standard",
  "summary": null
 },
 "temperature": 1.0
}
```

#### Google Interactions (generative baseline), POST /v1beta/interactions

File `evidence/probe-google-generative.json`. HTTP 200, 2010 ms (first request of its process, so it includes connection setup). Provider request ids: `{"server-timing": "gfet4t7; dur=1940"}`. The auth header is removed.

Request body:

```json
{
 "model": "gemini-4-hydrogen",
 "input": "Classify the customer message into exactly one banking customer-support intent from the list.\nReturn JSON with two fields: \"label\" (one intent from the list, copied exactly) and \"probability\" (your probability, from 0 to 1, that the label is correct).\n\nIntents:\n- billing\n- replacements\n- general\n\nCustomer message:\nThe blue mug I ordered on Monday arrived cracked on Wednesday.",
 "store": false,
 "generation_config": {
  "thinking_level": "low",
  "max_output_tokens": 4096
 },
 "response_format": {
  "type": "text",
  "mime_type": "application/json",
  "schema": {
   "type": "object",
   "properties": {
    "label": {
     "type": "string",
     "enum": [
      "billing",
      "replacements",
      "general"
     ]
    },
    "probability": {
     "type": "number"
    }
   },
   "required": [
    "label",
    "probability"
   ],
   "additionalProperties": false
  }
 }
}
```

Response body:

```json
{
 "status": "completed",
 "usage": {
  "total_tokens": 450,
  "total_input_tokens": 310,
  "input_tokens_by_modality": [
   {
    "modality": "text",
    "tokens": 310
   }
  ],
  "total_cached_tokens": 0,
  "total_output_tokens": 38,
  "output_tokens_by_modality": [
   {
    "modality": "text",
    "tokens": 38
   }
  ],
  "total_tool_use_tokens": 0,
  "total_thought_tokens": 102,
  "initial_input_tokens": 310
 },
 "created": "2026-11-14T17:02:10Z",
 "updated": "2026-11-14T17:02:10Z",
 "service_tier": "standard",
 "steps": [
  {
   "signature": "EvwDCvkDAWkUfRNmSLVzDLlt256iPH1eeLc2FmyhF1Y9pf3f6DkSBJQhIZz2iHtLM91YTel4w3bkodOfNmOZU5Ad5swMd2SnSWhKBAvnRX4SEGO7Uor6+BYkThJJrNbAnlGqtM8Xl8XgoUJvDtPrVehoraOTCZtWISTAhJrdQ6KFdt+cLttcyx/nP/kYMhz0ONBVswr3cYFttMAxl3rpy3y2gIgFpNZ9vk2dSnbiGFJNPxUtXvdx6BB434Fc284mJRraCAzgCVmigHFYBKyxROodIvqNyVRYR+6XbX5N/M9IxcX6aaJAjfXVq43xMp29heSEjiv5v/hVYfPnhKDbKvliYjts72jd3745WU2O5fynKc9hxfL2jiM1NW19E05ZdzaPPF0VovMk7xH2WWCBHmbuQnztXybu6dVLCgDrX1gIjQYbIPqa3pykj9pYRN0NxMaV7fve5NXA/m97j5Nz0QKsbKeKLaEbMoNHQ16YvdZHYzQ2sv8R2BhwJ4ccfmFvyUdNCeb5hsFsTtCMRuWNT+qunOlMZiqvqK7sBA9lt4TiPPz8HhPC2H0M+ByXzSyqg7a7ZCeI+C9f4thI3Vtu1TQ8lzaJspvyvzIzqeLuGg2rezGT1dO7RsvREJ0UyisAY9Py5ClC4qcP16vf51SqLmshtK+EOCSI7MJdoZeyrQ==",
   "type": "thought"
  },
  {
   "content": [
    {
     "text": "{\n  \"label\": \"replacements\",\n  \"probability\": 0.98\n}",
     "type": "text"
    }
   ],
   "type": "model_output"
  }
 ],
 "object": "interaction",
 "model": "gemini-4-hydrogen"
}
```

### Reliability (choice set)

**Jev 1.14**

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.2-0.3 | 1 | 0.250 | 0.000 |
| 0.3-0.4 | 3 | 0.347 | 0.000 |
| 0.4-0.5 | 15 | 0.456 | 0.400 |
| 0.5-0.6 | 22 | 0.543 | 0.455 |
| 0.6-0.7 | 28 | 0.652 | 0.571 |
| 0.7-0.8 | 28 | 0.738 | 0.643 |
| 0.8-0.9 | 40 | 0.845 | 0.650 |
| 0.9-1.0 | 263 | 0.982 | 0.943 |

**gpt-6-luna, Decisions API**

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.1-0.2 | 2 | 0.155 | 0.000 |
| 0.2-0.3 | 10 | 0.272 | 0.400 |
| 0.3-0.4 | 10 | 0.336 | 0.400 |
| 0.4-0.5 | 16 | 0.443 | 0.250 |
| 0.5-0.6 | 19 | 0.539 | 0.579 |
| 0.6-0.7 | 17 | 0.650 | 0.588 |
| 0.7-0.8 | 22 | 0.748 | 0.682 |
| 0.8-0.9 | 40 | 0.851 | 0.750 |
| 0.9-1.0 | 262 | 0.978 | 0.885 |

**Gemini Decision 1**

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.2-0.3 | 4 | 0.258 | 0.000 |
| 0.3-0.4 | 8 | 0.362 | 0.500 |
| 0.4-0.5 | 22 | 0.458 | 0.273 |
| 0.5-0.6 | 27 | 0.550 | 0.481 |
| 0.6-0.7 | 31 | 0.662 | 0.677 |
| 0.7-0.8 | 28 | 0.746 | 0.679 |
| 0.8-0.9 | 57 | 0.852 | 0.825 |
| 0.9-1.0 | 223 | 0.970 | 0.964 |

**gpt-6-luna, Responses API, effort none**

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.1-0.2 | 1 | 0.170 | 0.000 |
| 0.3-0.4 | 2 | 0.370 | 0.500 |
| 0.4-0.5 | 6 | 0.433 | 0.333 |
| 0.5-0.6 | 11 | 0.558 | 0.364 |
| 0.6-0.7 | 15 | 0.645 | 0.600 |
| 0.7-0.8 | 24 | 0.751 | 0.750 |
| 0.8-0.9 | 52 | 0.857 | 0.712 |
| 0.9-1.0 | 289 | 0.970 | 0.882 |

**Gemini 4 Hydrogen, thinking low (18 items only)**

| Stated probability | Items | Mean stated | Share correct |
| --- | --- | --- | --- |
| 0.8-0.9 | 1 | 0.850 | 0.000 |
| 0.9-1.0 | 17 | 0.974 | 0.882 |

### Latency

| Model | Set | Requests | p50 ms | p95 ms | min–max ms | Server p50 ms | Billed input tokens (mean) | Output tokens reported (mean) | Cost per 1,000 | Retried |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jev 1.14 | choice | 400 | 262 | 304 | 236–545 | n/a | 1685.8 | 826.3 | $0.0708 | 0 |
| gpt-6-luna, Decisions API | choice | 400 | 118 | 280 | 99–1097 | 66 | 984.6 | 0.0 | $0.0985 | 0 |
| Gemini Decision 1 | choice | 400 | 637 | 857 | 240–3565 | n/a | 1099.0 | 0.0 | $0.1099 | 6 |
| gpt-6-luna, Responses API, effort none | choice | 400 | 1188 | 1890 | 860–4276 | 903 | 974.5 | 22.1 | $0.1085 | 0 |
| Gemini 4 Hydrogen, thinking low (18 items only) | choice | 18 | 15175 | 34248 | 2763–56579 | n/a | 1485.6 | 122.4 | $3.1467 | 3 |
| Jev 1.14 | predicate | 400 | 253 | 307 | 225–850 | n/a | 412.7 | 21.0 | $0.0173 | 0 |
| gpt-6-luna, Decisions API | predicate | 400 | 123 | 257 | 95–651 | 72 | 285.1 | 0.0 | $0.0285 | 0 |
| Gemini Decision 1 | predicate | 400 | 475 | 644 | 193–1084 | n/a | 224.0 | 0.0 | $0.0224 | 1 |
| Jev 1.14 | score | 400 | 252 | 331 | 226–724 | n/a | 338.2 | 18.0 | $0.0142 | 0 |
| gpt-6-luna, Decisions API | score | 400 | 116 | 252 | 93–281 | 66 | 148.2 | 0.0 | $0.0148 | 0 |
| Gemini Decision 1 | score | 400 | 453 | 529 | 177–1111 | n/a | 135.3 | 0.0 | $0.0135 | 0 |

### One confident disagreement

Set: yes/no over a passage (BoolQ); item `boolq-420` (file `data/samples/predicate.jsonl`).

Passage (first 600 characters): A shoot-out is usually considered for statistical purposes to be separate from the match which preceded it. In the case of a two-legged fixture, the two matches are still considered either as two draws or as one win and one loss; in the case of a single match, it is still considered as a draw. This contrasts with a fixture won in extra time, where the score at the end of normal time is superseded. Converted shoot-out penalties are not considered as goals scored by a player for the purposes of their individual records, or for ``golden boot'' competitions.

Input or question: "do penalty shoot out goals count in golden boot"

Gold label: `False`.

gpt-6-luna, Decisions API: `True`, top probability 0.940, P(yes) 0.940.

Gemini Decision 1: `False`, top probability 0.989, P(yes) 0.011.

Other confident disagreements:

- `boolq-420` gold `False`: Jev 1.14 `False` at 0.94; gpt-6-luna, Decisions API `True` at 0.94

## Documentation against behaviour

- OpenAI predicate probabilities came back with two decimals and reached exact 0 or 1 on 287 of 396 BoolQ answers; the docs show two-decimal examples but do not state the rounding.
- OpenAI choice answers put probability exactly 1.0 on the top intent on 88 of 398 routing items.
- Jev 1.14, intent routing (BANKING77, 77 intents): top probability of 0.995 or more (shown as 1.00 at two decimals) on 129 items, right on 99.2% of them.
- Jev 1.14, 5-level sentiment (SST-5): top probability of 0.995 or more (shown as 1.00 at two decimals) on 10 items, right on 90.0% of them.
- gpt-6-luna, Decisions API, intent routing (BANKING77, 77 intents): top probability of 0.995 or more (shown as 1.00 at two decimals) on 88 items, right on 97.7% of them.
- gpt-6-luna, Decisions API, yes/no over a passage (BoolQ): top probability of 0.995 or more (shown as 1.00 at two decimals) on 287 items, right on 94.1% of them.
- gpt-6-luna, Decisions API, 5-level sentiment (SST-5): top probability of 0.995 or more (shown as 1.00 at two decimals) on 4 items, right on 75.0% of them.
- Gemini Decision 1, intent routing (BANKING77, 77 intents): top probability of 0.995 or more (shown as 1.00 at two decimals) on 56 items, right on 100.0% of them.
- gpt-6-luna, Decisions API score answers: `confidence` differs from TypeSafe's published formula by at most 0.005 and from the top probability by up to 0.290.
- Jev 1.14 score answers: `confidence` differs from TypeSafe's published formula by at most 0.005 and from the top probability by up to 0.360.
- Jev reports nonzero `output_tokens` (mean 21.0 on yes/no requests); the docs say output tokens are free, so they are not counted in spend.
- For the same routing request Jev billed 1686 input tokens on average and OpenAI 985; each provider counts with its own tokenizer and question formatting.
- gpt-6-luna, Decisions API returned `type: refusal` on 2 of 400 intent routing (BANKING77, 77 intents) items, all benign public-dataset text: `b77-1198` (request `req_9cb504cee0af4d9cb16fc321de967008`), `b77-707` (request `req_4ebb4dc89a3c41e7882033c2d2321a0c`). The docs allow refusals; they do not say when they happen.
- gpt-6-luna, Decisions API returned `type: refusal` on 4 of 400 yes/no over a passage (BoolQ) items, all benign public-dataset text: `boolq-124` (request `req_28a93da44a2a49e9afe947614dbdb5f0`), `boolq-1040` (request `req_103c09caebde4061a7ddb461ff3890f4`), `boolq-2644` (request `req_694920172b1441488b4923b1c2e36d90`), `boolq-998` (request `req_5be2be983de14c8da53fc0c9f8e82582`). The docs allow refusals; they do not say when they happen.
- Each added yes/no question cost 153.9 billed input tokens on OpenAI and 17.2 on Jev, for a question whose own text is about a dozen tokens. OpenAI's docs do not say what a question adds; Google's say each question adds tokens "for its own instructions, criteria, and formatting". In both cases the shared passage was billed once, not once per question.
- Google: the first API project was on prepaid billing with no credit left and returned HTTP 402; the measured runs used a second project on the free tier, where Gemini 4 Hydrogen allows 20 requests a day.

## Limits

- Public test sets. BANKING77, BoolQ and SST-5 have been public for years and may be in these models' training data; the accuracy here may be higher than on unseen traffic.
- 400 items per set, one wording per question type, no prompt tuning. Accuracy and calibration depend on the instructions and option descriptions.
- One machine and one network path. Latency includes the network to each provider and will differ elsewhere. The Jev and OpenAI runs overlapped in time.
- Prices are the published list prices on the read date; the providers' invoices were not checked.
- The OpenAI decision API returned probabilities rounded to two decimals, including exact 0 and 1, which limits the resolution of its calibration figures.
- The generative baseline states one probability for its own label. Its Brier score and ECE use that number only; its full distribution is unknown.
- Google ran about three hours after the other two, on the Gemini API free tier, from a second API project (the first project had no prepaid credit and returned HTTP 402). Gemini 4 Hydrogen, the Google generative baseline, covers only 18 routing items: its free tier allows 20 requests a day. Do not compare its accuracy.
- The fan-out test uses word-presence questions, which are easy; it measures billing and latency, not hard reasoning.

## Privacy scan

Every file under `.studio/ai-channel/decisions/` (except the downloaded datasets and saved documentation pages) was searched for each API key, each key's prefix, this account's home path, any home-directory path, the account user name and the host name. Counts are files with a match.

| Pattern | Files matching |
| --- | --- |
| GEMINI_API_KEY value | 0 |
| GEMINI_API_KEY prefix | 0 |
| OPENAI_API_KEY value | 0 |
| OPENAI_API_KEY prefix | 0 |
| JEV_API_KEY value | 0 |
| JEV_API_KEY prefix | 0 |
| home path | 0 |
| any home-directory path | 0 |
| account user name | 0 |
| host name | 0 |
