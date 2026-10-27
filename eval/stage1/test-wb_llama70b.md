# Stage 1 on the test split: wb_llama70b

Model `meta-llama/Llama-3.3-70B-Instruct`. 16 synthetic scenarios, 177 messages. Gold labels are the scenario labels written with the dataset (draft, not yet reviewed by a human).

| Measure | Value |
| --- | --- |
| Model unavailable (after retries) | 0 of 177 |
| Labelled messages found (any label) | recall 0.84, precision 0.72 |
| Ordinary-chat messages given a label | 0 of 41 |
| Latency per message | p50 412 ms, p95 531 ms |
| Cost | USD 0.1056 |
| Wall time, concurrency 4 | 19 s |

| Label | Precision | Recall | Gold count |
| --- | --- | --- | --- |
| berbagi_data_pribadi | 0.80 | 1.00 | 4 |
| kata_kasar | 1.00 | 1.00 | 2 |
| membangun_kedekatan | 0.50 | 1.00 | 4 |
| meminta_data_pribadi | 0.83 | 0.83 | 6 |
| meminta_kerahasiaan | 0.67 | 1.00 | 4 |
| menawarkan_hadiah | 0.50 | 1.00 | 3 |
| menekan_mengancam | 0.50 | 0.50 | 2 |
| menguji_batas | 0.50 | 1.00 | 1 |
| menyakiti_diri | 0.75 | 1.00 | 3 |
| perundungan | 0.50 | 0.22 | 9 |
| pindah_kanal | 1.00 | 1.00 | 3 |

Median signal on messages without gold labels: 0.0
