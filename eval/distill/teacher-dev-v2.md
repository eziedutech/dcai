# Distillation teacher on the dev split

Teacher: the reasoning pool (Muse Spark). 34 scenarios, 366 messages, 365 training examples written. Gold labels are the dataset drafts.

| Measure | Value |
| --- | --- |
| Teacher failed (after retries) | 1 {'LLMOutputInvalid': 1} |
| Labelled messages found (any label) | recall 0.86, precision 0.94 |
| Ordinary-chat messages given a label | 1 of 80 |
| Cost of priced calls | USD 0.5830 |
| Wall time, concurrency 4 | 312 s |
