# Handing work over: who does it (D0-D4) and how to keep it cheap

Read when a hand-over to a script, free model or helper is being set up and the always-on "Model routing" lines are not enough.

## D. Difficulty decides WHO does it (lowest tag that fits)
| Tag | The subtask... | Who |
|---|---|---|
| D0 | is deterministic: grep, jq, sed, count, reshape, short script, test run, `git diff --stat` | script, no AI |
| D1 | is one-shot text, text in and text out, no tools: label, classify, summarise, extract, rewrite, draft | `cheap-llm` (free); stronger model needed: `agy-ask`. [cheap-models.md](cheap-models.md) |
| D2 | needs files or tools, mechanical, checkable: the same edit over many files, search and summarise, log triage, conversion | `haiku-helper` subagent |
| D3 | is multi-file edits, review, moderate reasoning, checkable by tests | `sonnet-helper` subagent, only if I am a higher tier than Sonnet or the job is many turns in an already long session; otherwise me |
| D4 | is design, architecture, root cause, security, irreversible, ambiguous, the final answer to the owner, or something the owner asked me to judge; or is costly to verify, costly to fix if wrong, or cannot be briefed self-contained | me |

Searching or collecting with grep is D0 (a script), not a helper, even inside a D4 job such as a root-cause hunt.

## Where the tokens go (measured 2026-11-13, Sonnet prices)
- Every main turn re-sends the whole context. So the cost of a task is about: number of my turns x context size, plus what I write. Output tokens cost 5 times input tokens.
- Me reading: about $0.001 per KB, paid again (at a tenth) on every later turn. Me writing: about $0.004 per KB.
- One hand-over (a helper start or a free-model call): about $0.015 to $0.03 on my side, mostly the extra turn. A Haiku helper's own tokens cost close to nothing; free models count as 0.
- Loading a skill: about $0.02 per session. Always-on lines (measured 2026-11-14): about 2,400 tokens, about $0.01 at the first turn of a session, then a tenth of that per turn.

## Token savers
The saving comes from keeping bulk reading and long writing off the main model.
1. I do not read bulk input. Pass the file path (or pipe the file) to the script, free model or helper; take back a file plus a summary of at most 10 lines. To look at a big file use `wc` and `head -5`, never a full read.
2. Long output (labels, summaries, drafts, docstrings) is written by the free model or a helper straight into the FINAL file, with the check chained in the same command (`... > labels.csv && wc -l labels.csv`). No scratch file and no separate move or check turn: each extra turn costs about $0.006.
2a. One line of text per item taken out of code or files (docstrings, one-line descriptions): a script extracts the items with their full bodies, `cheap-llm` writes all lines in ONE call, a script inserts and checks. No `haiku-helper` in between (measured 2026-11-14 on 208 functions: free model 200 right, Haiku alone 125 right and dearer).
3. Size gate: hand over when more than about 20 KB would enter my context or I would write more than about 4 KB. Smaller than both: I do it myself. A script (D0) is always worth it. (First gate, measured 2026-11-13: 12 KB read or 2.5 KB written; raised after the second test showed hand-overs at that size still lost.)
4. A whole list goes in ONE call, never one call per item.
5. Check the result with a tool (count, grep, tests), not by reading it again.
6. Few turns: one script, or one batch of parallel tool calls, instead of many small steps.

## Rules
- Delegate only if ALL hold: output is cheap to verify, a wrong answer is cheap to fix, the prompt can be self-contained, and my doing it would cost clearly more tokens (bulk reading, many files, repetitive edits).
- Prompt: one task, exact input location or text, exact output format, length cap, "no explanation". Ask for the result, not the reasoning. Helpers end with a `CHECK:` line (how to verify) or `ESCALATE: <reason>`.
- Verify with a tool, never with a second model, and do nothing more than this:

| Output | Check |
|---|---|
| Code or edits | run the tests / linter / `node --check`; read `git diff --stat`, then only the hunks that matter |
| JSON / structured | parse it, compare to schema, spot-check 3 items against the source |
| Extraction / counts | grep or count in the source; sample at most 3 rows |
| Summaries / rewrites | confirm 3 named facts or numbers appear; do not re-read the whole thing |
| Drafted text (docstrings, descriptions, summaries) | `draft-check.py` finds empty, missing, duplicate, over-long and filler lines; I skim only the 3 lines it prints. Exit 1 = redo the whole batch one rung up |
| Bulk file work | file count and a `git status`; open 1 file at random |

- Check fails: retry once one rung up, then do it myself. Never more than one retry. A failed sample, or a helper that itself says "approximate" or "may need a read", means the whole batch failed: do not patch only the sampled item.
- Effort: default. "ultrathink" only for root-cause debugging after one failed attempt, architecture or migration planning, security review, ambiguous multi-constraint decisions; drop back right after. Never for lookups, edits, formatting or delegation prompts.
