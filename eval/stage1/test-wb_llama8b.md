# Stage 1 on the test split: wb_llama8b

Model `meta-llama/Llama-3.1-8B-Instruct`. 16 synthetic scenarios, 177 messages. Gold labels are the scenario labels written with the dataset (draft, not yet reviewed by a human).

| Measure | Value |
| --- | --- |
| Model unavailable (after retries) | 0 of 177 |
| Labelled messages found (any label) | recall 0.89, precision 0.52 |
| Ordinary-chat messages given a label | 5 of 41 |
| Latency per message | p50 373 ms, p95 439 ms |
| Cost | USD 0.0328 |
| Wall time, concurrency 4 | 17 s |

| Label | Precision | Recall | Gold count |
| --- | --- | --- | --- |
| berbagi_data_pribadi | 0.40 | 1.00 | 4 |
| kata_kasar | 0.67 | 1.00 | 2 |
| membangun_kedekatan | 0.29 | 1.00 | 4 |
| meminta_data_pribadi | 1.00 | 1.00 | 6 |
| meminta_kerahasiaan | 0.40 | 0.50 | 4 |
| menawarkan_hadiah | 0.43 | 1.00 | 3 |
| menekan_mengancam | 0.33 | 0.50 | 2 |
| menguji_batas | 0.25 | 1.00 | 1 |
| menyakiti_diri | 0.40 | 0.67 | 3 |
| perundungan | 0.43 | 0.33 | 9 |
| pindah_kanal | 1.00 | 0.67 | 3 |

Median signal on messages without gold labels: 0.0
