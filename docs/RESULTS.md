# Results

Seven tasks, each run once with route-task and once without. The figures are Claude tokens used. A free model's tokens count as 0.

| Task | Handled by (with route-task) | Without | With | Change |
|---|---|---:|---:|---:|
| Label 600 reviews | Free model `qwen3.8-27b` on Groq, 9 calls | 25,077 | 14,311 | **-43%** |
| Add a docstring to 60 code files | Script extracts, free model `gemini-2.5-flash-lite` writes, script inserts | 27,015 | 15,374 | **-43%** |
| Label 200 reviews, ambiguous | Free model `gemini-2.5-flash-lite`, 1 call | 19,111 | 10,690 | **-44%** |
| Index 20 reports | Claude with a script | 22,290 | 16,922 | **-24%** |
| Label 200 reviews | Free model `gemini-2.5-flash-lite`, 1 call | 11,719 | 10,308 | **-12%** |
| Label 20 reviews | Claude with a script | 7,058 | 9,741 | +38% |
| Summarise a 100 KB document | Claude with a script | 8,798 | 11,353 | +29% |
| **All seven** | | **121,068** | **88,699** | **-27%** |

Jobs under about 20 KB stay with Claude, because a handover would cost more than doing them. The rules themselves add a few thousand tokens to each session, which is why the smallest jobs come out a little higher.

## Correct answers

| Task | Without | With |
|---|---:|---:|
| Label 600 reviews | 580 | 599 |
| Docstrings, 60 files | 208 of 208 | 197 of 208 |
| Label 200 reviews, ambiguous | 196 | 200 |
| All other tasks | all correct | all correct |
