# Results

Each task ran with and without route-task. Numbers are Claude tokens for new input and output. Tokens re-read from the cache are left out, since they cost a fraction. Free-model tokens count as 0.

| Task | Without | With | Change | Correct without / with |
|---|---:|---:|---:|---|
| Label 600 reviews | 25,077 | 14,311 | **-43%** | 580 / 599 of 600 |
| Describe 60 code files | 27,015 | 15,374 | **-43%** | 208 / 197 of 208 |
| Label 200 reviews (hard) | 19,111 | 10,690 | **-44%** | 196 / 200 of 200 |
| Index 20 reports | 22,290 | 16,922 | **-24%** | all / all |
| Label 200 reviews | 11,719 | 10,308 | **-12%** | all / all |
| Label 20 reviews | 7,058 | 9,741 | +38% | all / all |
| Summarise a 100 KB doc | 8,798 | 11,353 | +29% | all / all |
| **All seven** | **121,068** | **88,699** | **-27%** | |

## Reading the table
- Savings grow with the amount of text. Free models do the bulk work, so Claude never reads or writes it.
- Small jobs and one-file summaries cost more. The rules add text, and Claude already reads a single file cheaply.
- Code descriptions from the free model were 11 of 208 less accurate than Claude's own. Check that output before you rely on it.
- The 600-review job took about 10 minutes, because the free tier rate-limited the big call and the tool retried in 9 pieces.
- Each run is one sample. Differences under about 15% are noise. The index task swung from +58% to -24% between two runs.
- Privacy, placement and remote-session rules passed in 20 of 21 scenario checks.
