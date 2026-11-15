# Measuring a skill: with versus without

Official method: at least three scenarios, a baseline without the skill, fresh instances. Ours automates it.

## Steps
1. Scenarios: build the combinations (axes of the skill, e.g. private or not, light or heavy, one worker or many, cheap to check or not). One JSON entry each: `id`, `group`, `mode` (`exec` = really run it in a scratch copy of synthetic fixtures; `plan` = answer with a route per subtask, nothing run), `prompt`, `expect` (labels that must appear; `A|B` = either), `forbid`, `verify` (shell test for executed tasks). Use synthetic data only. Example: `~/.claude/state/skill-tests/route-task/make_scenarios.py`.
2. Run: `python3 -I ~/.claude/skills/skill-optimizer/scripts/run_ab.py SCENARIOS.json OUTDIR --skill NAME` (resumable; one run at a time; `--only ID,ID` for a subset). The `without` arm uses an isolated config dir holding only the credentials link: no skill, no CLAUDE.md, no helper agents. The `with` arm adds the skill, CLAUDE.md and agents. Prompts never name the skill, so it must trigger by itself.
3. Report: `python3 -I ~/.claude/skills/skill-optimizer/scripts/report_ab.py OUTDIR "Title"` writes `report.md` (every prompt, tokens, cost, gain %, route and output result) and `report.html` (infographic).

## Metrics
- Tokens: input + output + cache read + cache creation over all models used (subagents included). Cost in USD is the fairer comparison because cached tokens are cheaper.
- Gain % = (without - with) / without. Negative means the skill cost more.
- `route_ok`: every expected label present and no forbidden label. `output_ok`: the `verify` command passed. `skill_used`: the Skill tool was called for it.

## Version 2 method (2026-11-13)
- Six scorecards, one per skill function. Gain % only for model routing (scorecard 1); privacy, placement, session rules and split/categorise are pass/fail; the skill's own overhead and load rate are shown separately.
- Three arms: `without`, `rules` (CLAUDE.md + helper agents, no skill), `with`. Compare `with` to `rules` to see what the skill itself adds. `--repeat 2` for steadier numbers.
- Empty task (`Z0`, one word reply) measures the fixed start-up cost per arm; gain is worked out on cost above it.
- `cost_norm` = cost with later-turn cache misses re-priced as hits. Use it for gain %, show billed cost beside it.
- Free-model calls (OmniRoute, agy) are counted from `~/.claude/routing.log` and priced at 0; show calls and KB.
- Executed runs use `--claude-args=--strict-mcp-config` so connected apps (about 41,000 extra tokens from turn 2) do not drown the result; report that cost as a separate finding.
- Every executed task has a tool check (`verify.py`); a cheaper wrong answer is not a saving.
- Build: `make_scenarios.py` -> `scenarios-v2.json`; report: `report_ab.py OUTDIR "Title" --baseline OLDDIR`.

## Version 3 method (2026-11-14)
- Two arms are enough once the rules live in CLAUDE.md: `without` and `with`. The report prints only the arms that were run.
- Test configs set `"syncClaudeAiSkills": false`. Otherwise Claude Code downloads the account's claude.ai skills in the background and drops their list (about 3,200 to 4,000 tokens) into whichever turn comes next, in either arm: pure timing luck that looked like a skill cost.
- When a number looks odd, look at it turn by turn in `runs/<tag>.raw.jsonl.gz` (cache write and cache read per main-model turn) before building a theory on totals.
- `skill_listed` must be False in every `without` run (clean baseline); the report checks it.
- Scorecard 6 for a skill whose rules are always on: overhead = the Z0 difference between the arms (tokens and dollars per session); skill loads on light tasks, target 0; pass marks, not load counts, judge the heavy and remote scenarios.
- Fixtures must need the route under test: a labelling list that a keyword script can pass tests the script, not the free model. Use semantic items for that.
- `allow_if` on a scenario lets a forbidden route pass when the plan states a named safeguard (for example "made-up data").
- The work root sits outside `~/.claude`, so the run cannot see the owner's real config.
- Caveats and findings go in a text file, one per line: `report_ab.py OUTDIR "Title" --baseline OLDDIR --notes FILE`. The baseline for a plan scenario is reused only when its prompt is identical.

## Known limits (state them in every report)
- Plan-only runs measure routing quality and planning cost, not real work savings; the label definitions are given in both arms.
- Free-model calls cost no Anthropic tokens; version 2 counts them as calls and KB at cost 0.
- One run per cell: results vary run to run; treat gains under about 15% as noise.
- Costs about $0.03 to $0.10 per run on Sonnet.

## Lessons from version 3 (2026-11-14)
- Check the account's usage allowance before a long test; a full run of 90 scenarios used about 4.7 million tokens and hit the weekly limit. Start with about 15 targeted runs; widen only if they leave a question open.
- Runs stopped by a limit report 0 tokens in about 5 seconds: set them aside (`limit-stopped/`) so the report counts only real runs and a later resume re-runs them.
- Work dirs are deleted after each run; recover what a helper did from `runs/<tag>.raw.jsonl.gz` (events with `parent_tool_use_id`).
- A prompt must say where the output file goes, or the check fails for a reason that has nothing to do with the skill.
- Read every plan answer marked wrong before counting it: a label or a too-narrow `allow_if` can fail a correct plan.
