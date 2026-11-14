# Privacy and licence scan

Run on 15 November 2026 over every file in this repository before the first commit.

Searched for:

- the value of every key, token or secret variable in the measuring workspace's `.env`, including `JEV_API_KEY`,
  `OPENAI_API_KEY` and `GEMINI_API_KEY` (compared inside the scan script; values never printed), and the key
  prefixes `sk-`, `AIza`, `ghp_`, `github_pat_`, `hf_`, `xox`, private-key blocks and bearer tokens;
- home-directory paths (`/home/...`, `/Users/...`), the account user name, the host name, and the committer's name
  and e-mail address;
- private IPv4 addresses (10.x, 172.16–31.x, 192.168.x);
- e-mail addresses, and processor and graphics-card model names.

Result: clean, no matches. Authorization headers in `evidence/` were already stored as `[REDACTED]` by the harness.
Response headers that identify a network path (`cf-ray`, `via` and similar) were dropped at capture time.

SST-5 text: every file was searched for each of the 2,210 sentences of the SST-5 test split, whole and as any
run of eight consecutive words. No file matches. The SST-5 sample is represented only by
`data/samples/score-ids.jsonl` (item ids and gold labels); `fetch_sst5.py` restores the text from the pinned upstream
file.

Names: apart from public Wikipedia text in the BoolQ passages, the only people named are dataset authors cited for
attribution in `README.md`. Company names (TypeSafe,
OpenAI, Google, PolyAI) appear as API providers or dataset publishers.
