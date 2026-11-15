# Project Overview
<!-- Last updated: TIMESTAMP -->
<!-- DYNAMIC FILE — updated automatically by AI agents every session as applicable -->

## Purpose
A Claude Code skill (`route-task`) plus always-on rules that make an agent spend the fewest Claude tokens for the same result: each part of a task goes to the cheapest rung that does it right (script, free model, Haiku helper, Sonnet helper, the main model), and heavy work goes to the right place (local, GitHub CI, a cloud session, Colab). Private data never leaves the machine. For Claude Code users who run bulk text work and long jobs.

## Stack & Key Dependencies
Markdown skills and rules; Node 18+ scripts (`cheap-llm.mjs`, `agy-ask.mjs`); Python 3 (`rs-guard.py`, test harness); POSIX shell. Needs Claude Code; free models need a local OmniRoute (optional).

## Architecture Overview
Tag each subtask: private? / D (difficulty, who) D0 script > D1 free model > D2 Haiku > D3 Sonnet > D4 main model / R (resources, where) R0 here > R1 CI > R2 cloud session > R3 Colab. Rules in `config/CLAUDE.routing.md` are always on; the skill loads only for remote sessions, Colab, agent teams and mixed private/outside cases.

## Important Directories
| Directory | Purpose |
|-----------|---------|
| `skills/` | `route-task` (procedures) and `skill-optimizer` (writing and A/B-testing skills) |
| `docs/`   | Documentation and AI memory |
| `agents/` | `haiku-helper`, `sonnet-helper` worker definitions |
| `config/` | Always-on routing rules, hook example, cloud-env example |
| `bin/` | `cheap-llm`, `agy-ask`, `rs-guard`, `rs-start` |

## Domain Terminology
D0-D4 difficulty tiers; R0-R3 resource tiers; P = private gate; size gate = 20 KB read / 4 KB written; ledger = remote-session log.

## Major Integration Boundaries
Claude Code remote sessions, GitHub CI, Google Colab, OmniRoute (free models), Google Antigravity CLI (`agy`).
