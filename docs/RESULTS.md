# Measured results (2026-11-14, made-up data only)

Each task ran with and without the skill (isolated config per arm). Gain is computed above the empty-task cost. Each task ran once; noise is about 15%.

| Task | Result |
|---|---|
| Label 600 items | 70% cheaper ($0.049 vs $0.164), 598/600 right |
| Label 200 items | 37% to 70% cheaper, 205/208 checks pass |
| Code descriptions | 55% cheaper |
| Keyword labelling | 12% cheaper |
| Summary / index / small | 1 to 4 cents dearer |
| Seven-task total | $0.457 vs $0.663 (31% cheaper) |

Privacy, placement, session and team rules held in every run.

Findings: the free tier rate-limits big inputs (the script retries in 9 KB pieces); the free-model call must run in the foreground with a 310 s timeout; each extra turn costs about $0.006; connected claude.ai apps add about 4.7 cents per session regardless of this skill.
