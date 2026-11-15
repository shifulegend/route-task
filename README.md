# route-task

Same result, fewer Claude tokens. A Claude Code skill and set of always-on rules that send each part of a task to the cheapest tool that does it right, and send heavy work to the right place.

![license](https://img.shields.io/badge/license-MIT-blue)

## What it does
- **Who does it (D0 to D4):** script > free model (`cheap-llm`, stronger `agy-ask`) > `haiku-helper` > `sonnet-helper` > the main model.
- **Where it runs (R0 to R3):** this machine > GitHub CI > cloud session > Colab.
- **Private data first:** bank, tax, mail, vault and credentials stay local; scripts refuse input that looks private.
- **Remote sessions:** naming, tags, limit of 4, ledger, archive order, enforced by a hook (`bin/rs-guard.py`).

## Measured result (made-up data, with vs without)
| Work | Claude cost |
|---|---|
| Bulk labelling / classifying | 37% to 70% cheaper |
| Code descriptions | 55% cheaper |
| Keyword labelling | 12% cheaper (noise) |
| Small tasks, summaries | 1 to 4 cents dearer (rules are extra text) |

Always-on rules add about 2,400 tokens (about 1 cent) per session. Details: `docs/RESULTS.md`.

## Install
```sh
git clone https://github.com/shifulegend/route-task && cd route-task
sh install.sh        # copies skills, agents, bin into ~/.claude (backs up first)
```
Then: append `config/CLAUDE.routing.md` to `~/.claude/CLAUDE.md`; merge `config/settings.hooks.example.json` into `~/.claude/settings.json`; copy `config/rs-cloud-envs.example.json` to `~/.claude/state/rs-cloud-envs.json` with your own environment ids.

Free models need a local OmniRoute (set `OMNIROUTE_BASE_URL`, `OMNIROUTE_API_KEY`). Without it, `cheap-llm` exits 3 and the rules fall back to Haiku.

## Customize
Add your own private-data words to the `PRIVATE` list in `bin/cheap-llm.mjs` and `bin/agy-ask.mjs` (bank names, client names). Edit host names and limits in the skill to match your setup.

## Layout
`config/` rules and examples · `skills/route-task` procedures · `skills/skill-optimizer` writing and A/B-testing skills · `agents/` helpers · `bin/` tools · `docs/` template memory

Built from the [golden-template](https://github.com/shifulegend/golden-template). License: MIT.
