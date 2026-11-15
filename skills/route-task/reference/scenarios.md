# Scenario matrix: which route fits

Five questions decide every case: private? / kind of work / weight / parallel? / cheap to verify? That is 2 x 4 x 4 x 3 x 2 = 192 combinations; SKILL.md collapses them to three tags: P (private), D (difficulty, who), R (resources, where). Rows below are worked examples. Mixed job: split it and route each step.

Codes: P = private data. Routes and their tags: SCRIPT = D0; CHEAP (cheap-llm), AGY (agy-ask) = D1; HAIKU = D2; SONNET = D3 (helper subagents); ME (orchestrator) = D4. No place named = R0 (this server); CI (GitHub CI) = R1; CLOUD (cloud child) = R2; COLAB = R3; TEAM (agent team) = modifier.

## One task, several routes (split first)
| Task | Subtask: route |
|---|---|
| Review a PR and say if it is faster | changed files and sizes: SCRIPT; benchmark: CLOUD; review of the hunks: SONNET; verdict to the owner: ME |
| Add a feature that needs a GPU check | design choice: ME; code and tests: SONNET; build/test: CI; tokens-per-second on GPU: COLAB; join and report: ME |
| Sort 300 public support mails and propose a policy | dedupe: SCRIPT; label all in one call: CHEAP `default`; read the 3 biggest groups and decide: ME |
| Reconcile a bank statement and write to the bank | totals and mismatches: SCRIPT (local); the mail: ME; nothing leaves this server (P applies to every subtask) |
| Find why a test fails only sometimes | collect logs and failing runs: HAIKU; three rival causes that must be argued: TEAM; the fix decision: ME |
| Small job (one file, a few lines) | no split: ME; a hand-over would cost more than the work |

## Private data (P always wins)
| Scenario | Route | Note |
|---|---|---|
| P, deterministic (totals from a bank CSV, ERP export reshape) | SCRIPT | local, no AI |
| P, needs judgement (tax query, bank mail, ERP design) | ME | Anthropic only; no helper, nothing leaves this server |
| P, heavy (90 MB dump, long run) | SCRIPT, streamed | 1.9 GB RAM: stream; never cloud, Colab or team |
| P, heavy, part of it holds no private data (test a new parser on a huge layout) | private part: SCRIPT here; the rest: CLOUD or COLAB with made-up data | cannot be separated: all stays here, tell the owner |
| P, bulk text that a cheap model could do | SCRIPT or ME | exit 4 from cheap-llm/agy-ask is final |

## Light work, not private
| Scenario | Route | Check |
|---|---|---|
| Count, rename, grep, dedupe CSV, reshape JSON, format convert | SCRIPT | output itself |
| Label or classify a list (commit types, tags) | CHEAP `default`, whole list in ONE call, output to a file | count lines; grep labels against the allowed set; sample 3 |
| The same, but under the size gate (about 20 KB to read, 4 KB to write) | ME | a hand-over would cost more |
| Yes/no, tagging, trivial transform | CHEAP `fast` | sample 3 |
| Regex, snippet, boilerplate | CHEAP `code` | run it |
| Summarise public text over ~100k tokens | CHEAP `long` | 3 named facts present |
| Puzzle or multi-step logic, no arithmetic | CHEAP `reason` | recompute one step |
| Needs a stronger model, one-off (hard rewrite, second draft, hard reasoning) | AGY | 30/day, never in a loop |
| Find usages across a repo, log triage, file summaries | HAIKU | grep or count in source |
| Same mechanical edit across many files | HAIKU | tests, `git diff --stat`, 1 random file |
| Multi-file feature edit with tests; one-angle review of a diff | SONNET | tests; read only the hunks that matter |
| 10 independent lookups or summaries | several HAIKU in parallel | not a team: they only report back |
| Root cause after a failed attempt; architecture; migration; security | ME (+ultrathink) | - |
| Result is hard to check or costly if wrong (legal or money wording, irreversible action) | ME | - |
| Final answer, or anything the owner asked me to judge | ME | - |
| Sequential steps, or several edits to one file | ME, single session | - |

## Heavy work, not private
| Scenario | Route | Note |
|---|---|---|
| Plain build or test of a GitHub repo | CI | push a branch; cheapest |
| Build/test over ~10 min or over 1.9 GB RAM, and an agent must fix failures | CLOUD (FulllAccess, `source_url`) | result on a branch |
| Many-core CPU benchmark | CLOUD | quiet and repeatable needed: COLAB cpu |
| Model download and load test up to 16 GB RAM | CLOUD | download inside the cloud VM |
| GPU test, GPU inference, tokens-per-second at sizes over 1.9 GB | COLAB | single script: `colab run` |
| About 100 GB scratch disk, or several hours (12 h free, 24 h paid); e.g. a 90 GB download that runs 8 hours | COLAB | download result before stop |
| Same script on T4 vs L4 vs A100 | COLAB, one prefixed session each | each counts toward the limit of 4 |
| Code work plus a GPU run (edit a repo, then time it on a GPU) | code edits by D (ME or a helper, here); COLAB for the GPU run; CLOUD only if the build or test is itself heavy | run uses made-up or public data |
| Evidence screenshots | CLOUD | permit in first prompt; save before archive |
| Light job that must run on the server itself | HAIKU/SONNET, or bridge child tagged `rs-local` | bridge offloads nothing |
| Long-lived service, root-level system change, must outlive the session | not Colab | host or cloud |

## Parallel work, not private
| Scenario | Route | Note |
|---|---|---|
| Review from several angles, reviewers cross-check each other | TEAM (3) | lead merges, I verify with tools |
| Debugging with competing hypotheses (intermittent 429, golden-output drift, ASan-only failure) | TEAM | one theory each |
| Feature across separate file sets (kernel, HTTP API, tests, docs), owners must coordinate | TEAM | one file set each |
| Same feature, owners need not talk | SONNET per file set | cheaper |
| Research compared across sources, conclusions challenged | TEAM | plain survey: ME or subagents |
| Multi-layer refactor, layer owners report API changes | TEAM | - |
| Parallel but compute-heavy | CLOUD or COLAB | never a team |
| Budget is tight, or routine edits | ME | - |

## Session handling
| Scenario | Action |
|---|---|
| Follow-up on a finished child's topic | reuse it with `send_message` (about $0.12 against $0.40 for a new child) |
| New topic | new child; same background for several children goes in one file |
| Fifth concurrent child or Colab session | wait: the guard blocks above 4 running |
| Child silent past its time | remote-sessions.md, "Watching" |
| Approval card on the phone, or mode problem | permissions.md |
| `elevated_session_untrusted_device` | never retry; use its branch/file output, tell the owner once |
| Check failed after delegating | retry once one rung up, then ME |
