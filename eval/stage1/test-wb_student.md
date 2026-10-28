# Stage 1 on the test split: wb_student

Model `wandb-artifact:///unismuh/dcai-distill/stage1-student-8b-v2-run:step1`. 18 synthetic scenarios, 197 messages. Gold labels are the scenario labels written with the dataset (draft, not yet reviewed by a human).

| Measure | Value |
| --- | --- |
| Model unavailable (after retries) | 0 of 197 |
| Labelled messages found (any label) | recall 0.78, precision 0.95 |
| Ordinary-chat messages given a label | 0 of 41 |
| Latency per message | p50 433 ms, p95 811 ms |
| Cost | USD 0.0411 |
| Wall time, concurrency 4 | 26 s |

| Label | Precision | Recall | Gold count |
| --- | --- | --- | --- |
| ajakan_berbahaya | 0.75 | 1.00 | 3 |
| berbagi_data_pribadi | 0.80 | 1.00 | 4 |
| kata_kasar | n/a | 0.00 | 3 |
| membangun_kedekatan | 1.00 | 0.75 | 4 |
| meminta_data_pribadi | 1.00 | 1.00 | 7 |
| meminta_kerahasiaan | 1.00 | 0.80 | 5 |
| menawarkan_hadiah | 0.60 | 1.00 | 3 |
| menekan_mengancam | 0.75 | 0.75 | 4 |
| menguji_batas | 1.00 | 1.00 | 1 |
| menyakiti_diri | 1.00 | 0.33 | 3 |
| perundungan | 0.60 | 0.33 | 9 |
| pindah_kanal | 1.00 | 1.00 | 3 |

Median signal on messages without gold labels: 0.0
