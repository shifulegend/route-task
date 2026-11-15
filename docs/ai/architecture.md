# Architecture
<!-- DYNAMIC FILE — updated by AI agents as architecture evolves -->
<!-- Last updated: TIMESTAMP -->

## System Overview
Task -> privacy gate -> split into subtasks -> tag D and R -> cheapest rung that works -> check with a tool -> retry one rung up on failure.

## Components
| Component | Responsibility | Technology |
|-----------|---------------|-----------|
| routing rules | `config/CLAUDE.routing.md` | always-on token-saving policy |
| skill | `skills/route-task` | remote sessions, Colab, teams, permissions |
| guard | `bin/rs-guard.py` | blocks non-compliant `create_session` |

## Data Flow
Large inputs are passed by file path to a script, free model or helper; only a file and at most 10 summary lines return to the main model.

## Integration Points
OmniRoute, Antigravity CLI, Claude Code remote sessions, Colab.
| Integration | Purpose | Auth Method |
|-------------|---------|-------------|
| OmniRoute | free models | optional |

## Key Design Decisions
<!-- Link to docs/ai/decision-log.md for full rationale -->
- see docs/ai/engineering-rules.md

## Known Constraints & Limitations
- see docs/ai/engineering-rules.md

## Security Boundaries
No secrets in this repo. Private data never goes to free models, CI, cloud or Colab; scripts refuse input that looks private (exit 4).
