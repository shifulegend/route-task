# Official guidance on token-efficient skills

Sources (checked 2026-11-13): code.claude.com/docs/en/skills; platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices; anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills.
Contents: 1 How loading works - 2 Limits - 3 Structure - 4 Description - 5 Writing rules - 6 Scripts - 7 Evaluation - 8 Frontmatter - 9 Our results

## 1. How loading works (progressive disclosure)
- Startup: only each skill's name and description are loaded.
- Skill used: the SKILL.md body loads and then stays in context across turns: "every line is a recurring token cost. State what to do rather than narrating how or why."
- Supporting files load only when Claude reads them; scripts are executed, not loaded (only output costs tokens).
- Referencing a supporting file from SKILL.md tells Claude what it holds and when to load it.

## 2. Limits and numbers
- SKILL.md under 500 lines; move detailed reference material out.
- After auto-compaction the most recent invocation of each skill is re-attached, keeping the first 5,000 tokens of each, within a combined 25,000-token budget. Put the most important instructions at the top. Re-invoking identical content adds an "already loaded" note, not a second copy.
- Description: max 1,024 characters (best-practices page). The skill listing truncates description plus `when_to_use` at 1,536 characters. The listing budget is 1% of the context window (`skillListingBudgetFraction`; env `SLASH_COMMAND_TOOL_CHAR_BUDGET`; `skillOverrides` value `"name-only"` shows names only).
- Name: at most 64 characters, lowercase letters, digits, hyphens.

## 3. Structure
- References one level deep from SKILL.md (deeper links get partially read).
- Reference files over 100 lines start with a table of contents.
- Descriptive file names (`reference/remote-sessions.md`, not `doc2.md`); forward slashes only.
- Put time-sensitive facts in a lessons or "old patterns" file, not in the rules.

## 4. Description
- Third person ("Routes tasks…", not "I route…").
- What it does AND when to use it, with the key terms a request would contain. Claude chooses the skill from the description alone, so a vague one means the skill is not used.

## 5. Writing rules
- "Claude is already very smart": only add context Claude does not already have; challenge each paragraph ("does it justify its tokens?").
- One consistent term per concept.
- Give a default, not many options.
- Examples convey more than rules; use a few short ones.
- Match freedom to fragility: exact steps or scripts for fragile operations, guidance for flexible ones.
- Checklists for multi-step work.

## 6. Scripts
Prefer a script for deterministic operations (parsing, counting, validating): more reliable and cheaper than generated code. State whether Claude should run it or read it.

## 7. Evaluation (official method)
- Build evaluations first: at least three scenarios; a baseline without the skill.
- Test with the models the skill will run on (Haiku, Sonnet, Opus); iterate by watching a fresh instance ("Claude B") use the skill, then fix what it missed.
- Our method with numbers: [evaluation.md](evaluation.md).

## 8. Claude Code frontmatter fields
`name`, `description`, `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context: fork`, `agent`, `background`, `hooks`, `paths`, `shell`. Substitutions: `$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`. Dynamic injection: a backticked command after `!` runs before the skill loads (a failing command aborts the invocation).
Use `disable-model-invocation: true` for skills that should only run when typed; the description then costs nothing at startup.

## 9. Our results
- 2026-11-13, `route-task`: one file of about 6,045 tokens (3,720 words, 160 lines) became a core of about 1,900 tokens plus 7 reference files read on demand. The tail (Colab, agent teams) used to fall outside the 5,000 tokens kept after compaction.
- Coverage check passed: all 123 backticked tokens and 49 numbers present in the new files.
