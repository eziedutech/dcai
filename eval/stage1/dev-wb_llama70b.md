# Stage 1 on the dev split: wb_llama70b

Model `meta-llama/Llama-3.3-70B-Instruct`. 34 synthetic scenarios, 366 messages. Gold labels are the scenario labels written with the dataset (draft, not yet reviewed by a human).

| Measure | Value |
| --- | --- |
| Model unavailable (after retries) | 0 of 366 |
| Labelled messages found (any label) | recall 0.88, precision 0.77 |
| Ordinary-chat messages given a label | 4 of 80 |
| Latency per message | p50 691 ms, p95 1476 ms |
| Cost | USD 0.2184 |
| Wall time, concurrency 4 | 72 s |

| Label | Precision | Recall | Gold count |
| --- | --- | --- | --- |
| berbagi_data_pribadi | 1.00 | 0.85 | 13 |
| kata_kasar | 1.00 | 0.75 | 4 |
| membangun_kedekatan | 0.50 | 0.67 | 9 |
| meminta_data_pribadi | 0.75 | 0.90 | 10 |
| meminta_kerahasiaan | 0.77 | 1.00 | 10 |
| menawarkan_hadiah | 0.70 | 1.00 | 7 |
| menekan_mengancam | 0.67 | 0.80 | 10 |
| menguji_batas | 0.57 | 0.80 | 5 |
| menyakiti_diri | 0.82 | 0.90 | 10 |
| perundungan | 0.69 | 0.60 | 15 |
| pindah_kanal | 0.43 | 0.75 | 4 |

Median signal on messages without gold labels: 0
