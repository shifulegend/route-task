# cheap-llm and agy-ask (NON-PRIVATE text only)

## cheap-llm (OmniRoute, free models): one-shot text jobs
`node ~/.claude/bin/cheap-llm.mjs --task default --max 800 < input.txt` (az: `node C:\Users\ASCO\.claude\bin\cheap-llm.mjs`)

| `--task` | Use for | Chain (first that answers) |
|---|---|---|
| `default` | extract, classify, reformat, short summary, rewrite | groq/openai/gpt-oss-120b (0.7 s) > groq/qwen/qwen3.8-27b > gemini/gemini-2.5-flash-lite |
| `fast` | trivial transforms, yes/no, tagging | groq/openai/gpt-oss-20b (0.3 s) > qwen3.8-27b > gpt-oss-120b |
| `code` | small snippets, regex, boilerplate (must be run or tested) | mistral/codestral-latest > gpt-oss-120b > gemini-2.5-flash-lite |
| `long` | big input; picked automatically above about 12 KB | gemini/gemini-2.5-flash-lite (1M) > nemotron-3-ultra :free (1M) |
| `reason` | puzzles, multi-step logic when a Claude tier is overkill | nemotron-3-ultra-550b :free (about 9 s) > gpt-oss-120b |

- Exit 3: every model failed; hand the job to `haiku-helper`. Exit 4: input looked private; never override it.
- One call per job. Free tiers rate-limit (429): do not loop.
- Big jobs (probe of 2026-11-13: 200 reviews = 12 KB and 600 reviews = 37 KB, each labelled in one call, all right):
  - Write to a file, never to my context: `node ~/.claude/bin/cheap-llm.mjs --system "<format, no explanation>" < in.txt > out.csv`, then `wc -l out.csv`.
  - Input over about 12 KB: nothing to set. The tool itself switches to the `long` chain (the Groq models refuse big input with http 413), allows up to 12000 output tokens and waits up to 140 s per model. `--max` and `--task long` are needed only to override that (about 3 tokens per short label line: 200 lines: 3000; 600 lines: 9000).
  - One call can take 3 minutes: give the Bash call a 300 s timeout.
- Weak spots: Groq qwen3.8 and codestral got a small time-arithmetic task wrong; no arithmetic with them.
- Table source: probe of 2026-11-06, one call each, all returned correct JSON extraction.

## agy-ask (Google's official Antigravity CLI, owner's Google AI Pro account)
For one-off jobs that need a stronger model than the free OmniRoute ones.
`node ~/.claude/bin/agy-ask.mjs --model gemini-3.8-flash-high < input.txt` (az: `node C:\Users\ASCO\.claude\bin\agy-ask.mjs`)

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
