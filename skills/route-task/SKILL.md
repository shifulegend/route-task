---
name: route-task
description: Procedures for work that leaves the main session or this server. Use before placing compute- or storage-heavy work (large builds, benchmarks, model downloads, GPU jobs, screenshots) on GitHub CI, a cloud session or Colab; before creating, messaging, watching, reusing or archiving a remote Claude session, Colab session or agent team; when private data and outside tools meet in one task; when an approval prompt or permission-mode problem appears; when the always-on routing rules do not settle a case. Not needed for light work (label, summarise, extract, edit, script): the always-on "Model routing" rules already cover it.
---

# route-task: procedures behind the always-on routing rules

Owner's goal: work smarter, not harder: the least tokens for the maximum output. Opus (the orchestrator, "me") decides, delegates and checks.
The "Model routing" lines in `~/.claude/CLAUDE.md` are always in context and decide the tags: P (private), D0-D4 (who), R0-R3 (where). This file holds only the procedures behind them. Loading it costs about one extra turn, so it is loaded only when a section below is needed.

## 0. Split first
1. Break the task into subtasks, each with one output that can be checked by itself.
2. Classify and route EACH subtask (section 1). One task may use several routes; independent subtasks run in parallel.
3. I join the results, verify them and give the final answer.
Keep a subtask with me when handing it over would cost more than it saves (size gate). Tag silently and act; write the tags out only in a plan the owner will read (`label 600 reviews: D1 R0, cheap-llm`).

## 1. Classify each subtask: P, then D, then R
**P. Private?** Touches private data: bank, tax, bank, tax, ERP, ITR, personal mail, vault, any credential: it stays on this server, done by a local script or me. Anthropic models only, or no AI. Never `cheap-llm`, `agy-ask`, R1-R3 or a team.
Private AND heavy: split it. The private part stays here (a script that streams the file, or me). Only a part holding no private data may go out, anything tested outside uses made-up data, and the plan line says "made-up data". Cannot be separated: all of it stays here, and I tell the owner if this server cannot handle it.

**D. Difficulty decides WHO does it** (lowest tag that fits): D0 script, no AI / D1 `cheap-llm` (free), stronger: `agy-ask` / D2 `haiku-helper` / D3 `sonnet-helper` / D4 me. The full table, the size gate, the prompt format and the checks: [reference/handover.md](reference/handover.md).

**R. Resources decide WHERE it runs** (a plain repo build or test is R1 whatever its size; otherwise the highest tag that fits):
| Tag | The subtask... | Where |
|---|---|---|
| R0 | fits this server | here |
| R1 | is a plain build or test of a GitHub repo | GitHub CI |
| R2 | exceeds this host: over ~1.9 GB RAM, build/test over ~10 min, big downloads, many-core benchmark, anything timed, evidence screenshots | cloud child: section 2 |
| R3 | needs a GPU, several hours, or about 100 GB of scratch disk | Colab: [reference/colab.md](reference/colab.md) |

Heavy work never runs on this server, not even "just to try".
- Code work plus a GPU run: the code edits are routed by D like any other edit (here, or a helper); only the GPU run goes to Colab (R3). A cloud child (R2) is added only if the build or test is itself too heavy for this server.
- Team: parallel AND the workers must talk to or challenge each other: agent team, [reference/agent-teams.md](reference/agent-teams.md). Parallel workers that only hand back a result are subagents (D2-D3), not a team.
- Anything else: me, single session. Unclear case: [reference/scenarios.md](reference/scenarios.md).
- Never, in any mode: force-push to a protected branch, relax branch protection, publish secrets or private data, delete the owner's data without a backup.

## 2. Remote-session protocol
The hook `~/.claude/bin/rs-guard.py` blocks `create_session` unless items 2-6 hold.
1. `get_session` (no argument). `permission_mode` is `plan`: stop, ask the owner to re-select Auto in the app.
2. Title `RS/<repo-or-area>/<task>/<YYYY-MM-DD>`; tags `rs-managed` plus the area.
3. `environment_id` of a cloud environment: `FulllAccess` `the heavy cloud environment id` (heavy compute) or `Default` `the default cloud environment id`. No id means the bridge, which is THIS machine and offloads nothing: only light jobs that need this host, tagged `rs-local`.
4. `permission_mode: auto`. Attach the repo with `source_url` + `clone_depth`; the child must not clone it itself.
5. First prompt is the only authority the child gets: goal, exact inputs, every permission (push, screenshots, downloads), what to leave alone, output location, a deadline, a hard stop ("no extra runs"), and "reply here in this chat only; do not message other sessions; do not request trust". At most ~400 words, pointing to files, not pasting them. Reply of at most 10 lines ending `CHECK:` or `ESCALATE:`.
6. At most 4 running (children and Colab sessions). Add a line to `~/.claude/state/rs-ledger.md`.
7. Model: `sonnet-5-5`; `opus-5-5` only for design, root cause, security or ambiguous work.

Afterwards: watch it (overdue: `get_session`, then its transcript newest-first), verify the result with a tool, confirm it is saved where it survives, mark the ledger line done, then `archive_session`. Never archive first. Same-topic follow-up: reuse the same child. Sweep `rs-managed` sessions at the start and end of work. Never send private data.
Full rules (environments, watching steps, archive, context economy): [reference/remote-sessions.md](reference/remote-sessions.md).

## 3. Reference files (read only the one the step needs)
| File | Read when |
|---|---|
| [reference/handover.md](reference/handover.md) | setting up a hand-over to a script, free model or helper and the always-on lines are not enough: D table, size gate, prompt format, checks |
| [reference/scenarios.md](reference/scenarios.md) | the tags do not settle a case; worked examples for every combination |
| [reference/cheap-models.md](reference/cheap-models.md) | a `cheap-llm` or `agy-ask` call needs more than the default command: task table, limits, exit codes |
| [reference/remote-sessions.md](reference/remote-sessions.md) | before creating, watching, reusing or archiving a child |
| [reference/colab.md](reference/colab.md) | before any Colab session |
| [reference/agent-teams.md](reference/agent-teams.md) | before forming a team |
| [reference/permissions.md](reference/permissions.md) | an approval card appears, a mode is wrong, or settings need changing |
| [reference/lessons.md](reference/lessons.md) | after an incident, or when the reason for a rule is needed |

## 4. Keep this skill current, without being asked
After any incident (stall, wrong environment, lost result, extra approval card, failed rung) append one dated line to [reference/lessons.md](reference/lessons.md); if a rule was missing, fix the rule file and the guard. A rule that decides a route goes into the "Model routing" lines of `~/.claude/CLAUDE.md` (keep them short: they are paid for on every turn of every session). New detail goes into a reference file, not here: this file stays in context on every turn once loaded and only its first 5,000 tokens survive a compaction.
