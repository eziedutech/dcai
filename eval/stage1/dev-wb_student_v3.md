# Stage 1 on the dev split: wb_student_v3

Model `wandb-artifact:///unismuh/dcai-distill/stage1-student-8b-v3-run:step1`. 40 synthetic scenarios, 424 messages. Gold labels are the scenario labels written with the dataset (draft, not yet reviewed by a human).

| Measure | Value |
| --- | --- |
| Model unavailable (after retries) | 0 of 424 |
| Labelled messages found (any label) | recall 0.81, precision 0.94 |
| Ordinary-chat messages given a label | 1 of 80 |
| Latency per message | p50 454 ms, p95 871 ms |
| Cost | USD 0.0885 |
| Wall time, concurrency 4 | 64 s |

| Label | Precision | Recall | Gold count |
| --- | --- | --- | --- |
| ajakan_berbahaya | 1.00 | 0.55 | 11 |
| berbagi_data_pribadi | 1.00 | 0.92 | 13 |
| kata_kasar | 1.00 | 0.25 | 4 |
| membangun_kedekatan | 1.00 | 0.56 | 9 |
| meminta_data_pribadi | 0.70 | 0.70 | 10 |
| meminta_kerahasiaan | 0.83 | 0.91 | 11 |
| menawarkan_hadiah | 0.73 | 0.89 | 9 |
| menekan_mengancam | 0.90 | 0.75 | 12 |
| menguji_batas | 1.00 | 0.60 | 5 |
| menyakiti_diri | 0.89 | 0.80 | 10 |
| perundungan | 0.75 | 0.60 | 15 |
| pindah_kanal | 0.80 | 0.80 | 5 |

Median signal on messages without gold labels: 0.0
