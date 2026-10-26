# Stage 1 on the dev split: wb_llama8b

Model `meta-llama/Llama-3.1-8B-Instruct`. 34 synthetic scenarios, 366 messages. Gold labels are the scenario labels written with the dataset (draft, not yet reviewed by a human).

| Measure | Value |
| --- | --- |
| Model unavailable (after retries) | 0 of 366 |
| Labelled messages found (any label) | recall 0.86, precision 0.53 |
| Ordinary-chat messages given a label | 24 of 80 |
| Latency per message | p50 672 ms, p95 1434 ms |
| Cost | USD 0.0677 |
| Wall time, concurrency 4 | 70 s |

| Label | Precision | Recall | Gold count |
| --- | --- | --- | --- |
| berbagi_data_pribadi | 0.80 | 0.92 | 13 |
| kata_kasar | 0.40 | 0.50 | 4 |
| membangun_kedekatan | 0.39 | 0.78 | 9 |
| meminta_data_pribadi | 0.67 | 0.80 | 10 |
| meminta_kerahasiaan | 0.75 | 0.90 | 10 |
| menawarkan_hadiah | 0.56 | 0.71 | 7 |
| menekan_mengancam | 0.40 | 0.40 | 10 |
| menguji_batas | 0.19 | 0.80 | 5 |
| menyakiti_diri | 0.60 | 0.60 | 10 |
| perundungan | 0.31 | 0.53 | 15 |
| pindah_kanal | 0.80 | 1.00 | 4 |

Median signal on messages without gold labels: 0
