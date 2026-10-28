# Stage 1 on the dev split: wb_student

Model `wandb-artifact:///unismuh/dcai-distill/stage1-student-8b-v2-run:step1`. 40 synthetic scenarios, 424 messages. Gold labels are the scenario labels written with the dataset (draft, not yet reviewed by a human).

| Measure | Value |
| --- | --- |
| Model unavailable (after retries) | 1 of 424 |
| Labelled messages found (any label) | recall 0.82, precision 0.91 |
| Ordinary-chat messages given a label | 2 of 80 |
| Latency per message | p50 783 ms, p95 7103 ms |
| Cost | USD 0.0883 |
| Wall time, concurrency 4 | 243 s |

| Label | Precision | Recall | Gold count |
| --- | --- | --- | --- |
| ajakan_berbahaya | 0.67 | 0.55 | 11 |
| berbagi_data_pribadi | 0.92 | 0.92 | 13 |
| kata_kasar | 1.00 | 0.25 | 4 |
| membangun_kedekatan | 1.00 | 0.56 | 9 |
| meminta_data_pribadi | 0.73 | 0.80 | 10 |
| meminta_kerahasiaan | 1.00 | 0.91 | 11 |
| menawarkan_hadiah | 0.70 | 0.78 | 9 |
| menekan_mengancam | 0.71 | 0.83 | 12 |
| menguji_batas | 1.00 | 0.80 | 5 |
| menyakiti_diri | 1.00 | 0.60 | 10 |
| perundungan | 0.85 | 0.73 | 15 |
| pindah_kanal | 0.67 | 0.80 | 5 |

Median signal on messages without gold labels: 0.0
