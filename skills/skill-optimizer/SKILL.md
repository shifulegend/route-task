---
name: skill-optimizer
description: Guides writing, shrinking, splitting and testing Claude Code skills so they cost the fewest tokens without losing content (progressive disclosure, size limits, description rules, compaction survival, with-versus-without-skill measurement). Use when creating or editing a SKILL.md, reducing a skill's token cost, splitting a skill into reference files, checking that a rewrite lost nothing, or measuring whether a skill actually saves tokens.
---

# skill-optimizer

Based on Anthropic's official guidance (checked 2026-11-13). Full rules: [reference/guidance.md](reference/guidance.md).

## Rules that decide most cases
1. SKILL.md is paid on every turn once loaded: keep it a short core (target under 2,000 tokens; hard limit 500 lines). Most important rules first: only the first 5,000 tokens survive a compaction.
2. Detail goes in `reference/*.md`, one level deep, each linked from SKILL.md with a "read when" line. Reference files cost nothing until read. Files over 100 lines get a contents line.
3. Anything deterministic goes in `scripts/`: a script is run, only its output costs tokens.
4. Description: third person, what it does plus when to use it, key words first, at most 1,024 characters.
5. State what to do, not why. Add only what Claude does not already know. One term per idea, one default instead of a menu. Dated facts and history go in a lessons file.

## Procedure to optimize an existing skill
1. Back it up to `~/.claude/backups/<skill>-SKILL.md.pre-<change>`.
2. Sort every paragraph: always-needed core / needed in one situation (reference file) / history (lessons file) / deterministic (script).
3. Rewrite the core as a decision table or checklist; keep pointers in other files (CLAUDE.md, hooks) valid by keeping the headings they name.
4. Prove nothing was lost: `python3 -I ~/.claude/skills/skill-optimizer/scripts/coverage_check.py <backup> <skill folder>`; review each miss by hand.
5. Prove it still works and saves tokens: [reference/evaluation.md](reference/evaluation.md).

## Reference files
| File | Read when |
|---|---|
| [reference/guidance.md](reference/guidance.md) | the full official rules, limits and numbers, or a rule needs checking |
| [reference/evaluation.md](reference/evaluation.md) | testing a skill with and without it, scoring routes, reporting gain % |
