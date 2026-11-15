# Agent teams (experimental)

Source: code.claude.com/docs/en/agent-teams (researched 2026-11-13).

## What it is
One session is the team lead; teammates each run in their own context window, share a task list and can message each other directly (subagents only report back to the caller).
- Off by default: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (shell or settings.json `"env"`). Interactive sessions only (not `-p` or SDK runs).
- STATUS HERE: enabled 2026-11-13 by the owner (settings.json env; backup `backups/settings.json.pre-agent-teams`); applies to sessions started after the change.
- Display: `teammateMode` in settings = `in-process` (default) | `auto` | `tmux` | `iterm2`.
- Hooks: `TeammateIdle`, `TaskCreated`, `TaskCompleted` (exit 2 blocks/keeps working).

## Cost reality (docs)
- Significantly more tokens than one session, scaling with the number of active teammates.
- Docs advise 3-5 teammates, 5-6 tasks each; "three focused teammates often outperform five scattered ones".
- Teammates inherit the lead's permission mode; their permission prompts surface in the lead session.
- Limits: no resume of in-process teammates, task status can lag, one team per session, no nested teams, no worktree isolation (split work by file ownership).

## Ladder position (use the cheapest that works)
script > cheap-llm > helper subagent (haiku/sonnet-helper: result-only tasks) > single session > remote child session (heavy compute) > agent team.
A team is worth its extra tokens ONLY when the work is parallel AND the workers must talk to each other or challenge each other's findings. Workers only hand back a result: subagents. Heavy compute: cloud child or Colab.

## Use a team
1. Code or PR review from several angles (correctness, security, performance, tests) where reviewers cross-check each other's findings before the lead merges them.
2. Debugging with competing hypotheses: each teammate tests one theory and argues against the others (project-zero: intermittent 429, golden-output drift, ASan-only failure).
3. A new feature spanning separate file sets (engine kernel, HTTP API, tests, docs) with clear file ownership and a shared task list.
4. Research that must be compared across sources (competitor or paper survey, several benchmark methodologies) where teammates challenge each other's conclusions.
5. Large multi-layer refactors where each layer owner reports API changes to the others as they go.

## Do NOT use a team
- Sequential steps, or several workers editing the same file: single session.
- Independent lookups, bulk classification, file searches, log triage: subagents or cheap-llm.
- Builds, test suites, benchmarks, downloads: remote child, GitHub CI or Colab.
- Anything private (bank, tax, ERP): never delegated, so no team either.
- Routine edits, or when the owner's budget is tight: single session.

## Rules when used
- Start with 3 teammates (max 5); each gets one named role, one file set and one deliverable; the lead's prompt states a hard stop and a deadline.
- Ask for results as files or a short summary; the lead integrates; I verify with tools, not with another model.
- Name teammates with the `RS/` style prefix of the task; log the team in the ledger as kind `team`; shut down all teammates by name when done (shutdown can be slow: check it ended).
- Record the first real use in lessons.md (tokens used against a single-session estimate) before using teams again.
