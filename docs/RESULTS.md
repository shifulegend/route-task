# Results

Each task ran with and without route-task. Numbers are Claude tokens for new input and output. Tokens re-read from the cache are left out, since they cost a fraction. Free-model tokens count as 0.

| Task | Without | With | Change |
|---|---:|---:|---:|
| Label 600 reviews | 28,823 | 9,046 | **-69%** |
| Describe 60 code files | 36,403 | 11,554 | **-68%** |
| Label 200 reviews (hard) | 18,199 | 11,029 | **-39%** |
| Label 200 reviews | 11,438 | 9,779 | **-15%** |
| Label 20 reviews | 6,947 | 9,642 | +39% |
| Summarise a 100 KB doc | 8,967 | 11,030 | +23% |
| Index 20 reports | 13,250 | 20,875 | +58% |
| **All seven** | **124,027** | **82,955** | **-33%** |

Output was correct in every run. The 600-review run got 598 right.

## Reading the table
- Savings grow with the amount of text. The 600-review job needs 9 free-model calls instead of 600 lines in Claude's context.
- Small jobs and file summaries cost more. The rules add text, and Claude already reads files cheaply with search. Below about 20 KB the rules tell Claude to do the job itself.
- Each run is one sample. Differences under about 15% are noise.
- Privacy, placement and remote-session rules passed in 20 of 21 scenario checks.
