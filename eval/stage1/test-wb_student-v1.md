# Stage 1 on the test split: wb_student

Model `wandb-artifact:///unismuh/dcai-distill/stage1-student-8b-run:step1`. 16 synthetic scenarios, 177 messages. Gold labels are the scenario labels written with the dataset (draft, not yet reviewed by a human).

| Measure | Value |
| --- | --- |
| Model unavailable (after retries) | 0 of 177 |
| Labelled messages found (any label) | recall 0.73, precision 0.84 |
| Ordinary-chat messages given a label | 0 of 41 |
| Latency per message | p50 476 ms, p95 1227 ms |
| Cost | USD 0.0326 |
| Wall time, concurrency 4 | 29 s |

| Label | Precision | Recall | Gold count |
| --- | --- | --- | --- |
| berbagi_data_pribadi | 0.80 | 1.00 | 4 |
| kata_kasar | n/a | 0.00 | 2 |
| membangun_kedekatan | 1.00 | 0.75 | 4 |
| meminta_data_pribadi | 0.86 | 1.00 | 6 |
| meminta_kerahasiaan | 1.00 | 1.00 | 4 |
| menawarkan_hadiah | 0.50 | 1.00 | 3 |
| menekan_mengancam | 0.50 | 0.50 | 2 |
| menguji_batas | 1.00 | 1.00 | 1 |
| menyakiti_diri | n/a | 0.00 | 3 |
| perundungan | 0.50 | 0.33 | 9 |
| pindah_kanal | 1.00 | 1.00 | 3 |

Median signal on messages without gold labels: 0.0
