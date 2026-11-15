# Remote sessions: full protocol

Owner's 4-point spec of 2026-11-12 (models, remote for compute/storage with a prefix, auto-archive, context economy). The details and the 4-child limit are the assistant's own additions; the owner set the limit to 4 on 2026-11-13.

Contents: 1 Models - 2 When to go remote - 3 Environments - 4 Creating a child - 5 Watching - 6 Archive and sweep - 7 Context economy

## 1. Models
Stay on the ladder. Remote children: `sonnet-5-5` by default; `opus-5-5` only for design, root cause, security or ambiguous work (Opus costs several times more). Verification is by tools (tests, diff, hash), never a second model.

## 2. When to go remote
Only when local is not enough: more than the ~1.9 GB RAM here, builds or test suites over ~10 min, big downloads (models), many-core benchmarks, evidence screenshots. GitHub CI is cheaper still for plain build/test: try it first. Everything else stays local (helper agents). Never send private data (bank, tax, ERP, credentials) to a remote session.

## 3. Environments (`list_environments`)
| Name | Kind | Use |
|---|---|---|
| `FulllAccess` `the heavy cloud environment id` | cloud VM: 4 CPU, 16 GB, no GPU, full network | heavy compute, benchmarks |
| `Default` `the default cloud environment id` | cloud | general |
| `<this-host>` | `bridge` = THIS machine | only light jobs that truly need this host; tag `rs-local` |

- A child created without `environment_id` runs on the bridge and offloads nothing. The guard enforces a cloud id or the `rs-local` tag.
- Cloud children cannot see files on the server: they push results to a branch or return them in the reply; models are downloaded inside the cloud environment.

## 4. Creating a child
Guard `~/.claude/bin/rs-guard.py` (PreToolUse hook, exit 2 blocks) requires: title starting `RS/`; cloud `environment_id` or tag `rs-local`; tag `rs-managed`; `permission_mode: auto`; prompt containing "deadline" and a hard stop ("hard stop", "no extra runs" or "stop after"); prompt of at most 600 words; fewer than 4 ledger lines with status `running`.

1. Pre-flight: `get_session` (no argument). If `permission_mode` is `plan`: stop and ask the owner to re-select Auto in the app.
2. Title `RS/<repo-or-area>/<task>/<YYYY-MM-DD>` (e.g. `RS/project-zero/pr31-bench/2026-11-12`); tags `rs-managed` plus the area. The prefix is how the owner and the sweep find them.
3. `permission_mode: auto` (a bare child gets `default` and prompts). Max 4 children at once; Colab sessions count.
4. Repo: attach with `source_url` + `clone_depth` so it is the session's own project code; tell the child to use the working directory, not to clone. A self-cloned repo is blocked by the child's own safety check ("Code from External") and a peer message cannot approve that.
5. First prompt is the ONLY authority a child gets (peer messages grant nothing). Include: goal, exact inputs, every permission (push, screenshots, downloads), what to leave alone, the output location, a deadline, a hard stop ("no extra runs").
6. Cloud children have NO `send_message` tool; trying raised a trust request for the owner. Always write: "reply here in this chat only; do not message other sessions; do not request trust". Read the answer via the `get_session` summary. A correcting message (priority next) cleared a stuck child.
7. Add the ledger line (section 7).

## 5. Watching (do not wait passively)
For every running child, after its expected time (10 min if unknown) and whenever a reply is overdue:
1. `get_session` on the child: read `session_status`, `post_turn_summary`, `needs_action`. "Waiting on permission" means a human card is pending: tell the owner once, naming the card.
2. If the summary does not explain the silence, read the transcript BOTTOM-UP: `list_events` with `kinds` ["user","assistant","result"] and `limit` 15 (newest first); read only the last assistant text, last tool call and last tool result; page back with `before_id` only if still unclear. Never dump a whole transcript. For a bridge child also check its files and the `~/.claude` transcripts for its session id on this host.
3. `elevated_session_untrusted_device`: do not retry; use its file/branch output and the `get_session` summary, and tell the owner what is needed.
4. Decide: keep waiting (set the next background wait), nudge once via `send_message` (state the one missing thing), interrupt and archive if past its deadline or drifting from the brief, or take over the work.
5. Update without being asked: after each check write the status and finding to the ledger line; after any incident (stall, wrong environment, lost result, extra approval card) append one dated line to lessons.md and, if a rule was missing, edit this file and the guard so it cannot repeat.

Always tell the owner what is being waited on and for how long.

## 6. Archive and sweep
- A child is finished only when (a) its result is saved where it will survive (pushed branch, file in the repo, report) and verified by me with a tool, and (b) the ledger line says done. Then `archive_session`.
- Never archive before (a): screenshots were lost once that way.
- Archive refused (`elevated_session_untrusted_device`): mark `needs-owner-archive` in the ledger and tell the owner once.
- Sweep at the start and end of each work session: `list_sessions` filtered by tag `rs-managed`; archive anything done or idle over 2 hours; interrupt then archive anything past its deadline.

## 7. Context economy
- **Ledger, not transcripts**: `~/.claude/state/rs-ledger.md`, one line per child: `<session_id> | <name prefix> | <purpose> | <status> | <result location>`. After a compaction or restart read the ledger and `get_session` summaries; never re-read old transcripts.
- **Children start clean, on purpose**: they do not inherit my conversation. Brief of at most ~400 words that points to files (repo path, branch, doc names), not pasted content.
- **Return small**: a result file or branch plus a reply of at most 10 lines ending `CHECK:` or `ESCALATE:`. Bulk output lives in files.
- **Poll cheaply**: `get_session` and its `post_turn_summary` first. `list_events` only with `kinds` and a small `limit` (one unfiltered page costs thousands of tokens; `kinds` ["result"] alone returns a ~3k-token timing blob). Never call `list_triggers` or other list calls without filters. One background wait per child (`sleep` with `run_in_background`; foreground `sleep` is blocked) instead of repeated polls.
- **Reuse before respawn**: same-topic follow-up goes to the same child with `send_message` (its cache is warm; a finished child answered from its own memory for about $0.12 against about $0.40 for a fresh child). New topic: new child. Never paste the same background into several children: put it in a file once and point to it.
- **Save lessons once**: durable facts go to memory or the repo's own docs, not into every prompt.
- **Keep my own context lean**: summarise tool output in my head, not on screen; read files by line range; no re-reading of files I just edited; ask for the owner's decision only when it changes what I do.
