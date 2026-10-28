# Distillation teacher on the dev split

Teacher: the reasoning pool (Muse Spark). 40 scenarios, 424 messages, 424 training examples written. Gold labels are the dataset drafts.

| Measure | Value |
| --- | --- |
| Teacher failed (after retries) | 0  |
| Labelled messages found (any label) | recall 0.84, precision 0.93 |
| Ordinary-chat messages given a label | 1 of 80 |
| Cost of priced calls | USD 0.6873 |
| Wall time, concurrency 4 | 365 s |
