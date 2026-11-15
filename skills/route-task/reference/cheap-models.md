# cheap-llm and agy-ask (NON-PRIVATE text only)

## Setup (first use, once): pick a backend
`cheap-llm` talks to any OpenAI-compatible endpoint. If it exits 3 with "no backend configured", ask the owner ONCE which they want, then write `~/.claude/cheap-llm.json` (template: `config/cheap-llm.example.json` in the repo). Never invent or guess a key; the owner supplies it as an environment variable.
1. **OmniRoute** (recommended: one local endpoint, your own routing/combos/fallbacks decide the model, free tiers pooled). Keep `base_url` at your OmniRoute (default `http://127.0.0.1:20128/v1`), key in `OMNIROUTE_API_KEY`, chains `["auto"]` or your combo names. Routing is the owner's: edit it in OmniRoute, not here.
2. **Provider API keys** (no OmniRoute): set `base_url` and `api_key_env` for one provider (Groq, Gemini OpenAI-compatible endpoint, OpenRouter, Mistral, OpenAI...) and list that provider's model ids in `chains`. Fall-back models in a chain can be any ids the endpoint serves.
3. **Neither**: skip D1; use `haiku-helper` for D2 work. The saving is smaller but nothing breaks.
Optional in the same file: `piece_chain` (models for the 9 KB retry), `private_words` (your own names that must never leave the machine: banks, clients).

## cheap-llm: one-shot text jobs
`node ~/.claude/bin/cheap-llm.mjs --task default --max 800 < input.txt`

`--task` picks a chain from your config (`default`, `fast`, `code`, `long`, `reason`; unset ones use `default`). Suggested meaning:

| `--task` | Use for |
|---|---|
| `default` | extract, classify, reformat, short summary, rewrite |
| `fast` | trivial transforms, yes/no, tagging |
| `code` | small snippets, regex, boilerplate (must be run or tested) |
| `long` | big input; picked automatically above about 12 KB |
| `reason` | puzzles, multi-step logic when a Claude tier is overkill |

- Exit 3: every model failed; hand the job to `haiku-helper`. Exit 4: input looked private; never override it.
- One call per job. Free tiers rate-limit (429): do not loop.
- Big jobs (probe of 2026-11-13: 200 reviews = 12 KB and 600 reviews = 37 KB, each labelled in one call, all right):
  - Write to a file, never to my context: `node ~/.claude/bin/cheap-llm.mjs --system "<format, no explanation>" < in.txt > out.csv`, then `wc -l out.csv`.
  - Input over about 12 KB: nothing to set. The tool itself switches to the `long` chain (the Groq models refuse big input with http 413), allows up to 12000 output tokens and waits up to 140 s per model. `--max` and `--task long` are needed only to override that (about 3 tokens per short label line: 200 lines: 3000; 600 lines: 9000).
  - One call can take 3 minutes: give the Bash call a 300 s timeout.
- Weak spots: small free models get arithmetic wrong; use a script for numbers.

## agy-ask (optional: Google's official Antigravity CLI, needs your own Google account)
For one-off jobs that need a stronger model than the free OmniRoute ones.
`node ~/.claude/bin/agy-ask.mjs --model gemini-3.8-flash-high < input.txt`

- Models: `gemini-3.8-flash-high` (default, about 12 s), `claude-sonnet-4-6`, `claude-opus-4-6-thinking` (hardest reasoning that is still non-private; saves Anthropic usage), `gpt-oss-120b-medium`.
- Limits: min 10 s between calls; max 30 per day; one call at a time per host; headless in an empty temp dir (any tool needing permission is auto-denied); refuses when the host has under 450 MB free RAM (one call peaks at about 270 MB).
- Exit 3: failed or limit; fall to `haiku-helper`. Exit 4: looked private.
- Personal account: never loop, never batch-call it. Automated volume got the first account banned.
- Only through the official `agy` CLI. Never the old proxy/adapter (uninstalled).

## Seeing what was routed
`~/.claude/routing.log` gets one line per `cheap-llm` or `agy-ask` call (time, tool, model, sizes). If it is empty after a work day, routing is not happening: say so instead of pretending.

## Keeping the table honest
When a model changes or a rung starts failing, re-run a small probe (one call per model, 8 s gaps, stop after 2 network failures in a row), then edit the table above.
- Big input that every long-input model refuses (usually a free-tier rate limit, http 429) is retried by the tool itself in pieces of about 9 KB on the short-input models; nothing to do on my side. Allow the full 300 s. Measured 2026-11-14: 600 reviews (80 KB) in 9 pieces, 230 s, 587 of 600 right.
