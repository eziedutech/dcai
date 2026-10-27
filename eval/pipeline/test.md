# Pipeline on the test split

16 synthetic scenarios, 177 messages, each played message by message through stage 1, the rule floor and stage 2. Expected levels are the dataset drafts, not yet reviewed by a person.

| Measure | Result | Spec target |
| --- | --- | --- |
| Risky approach reaching waspada or higher | 4 of 4 | 0.9 |
| Ordinary and hard cases reaching waspada or higher | 1 of 7 | at most 0.1 |
| Detection delay (messages after the expected start), median | 2 (n=11) | at most 2 |
| Risky scenarios never raised above aman | 0 | |
| Final level exactly as expected | 12 of 16 | |
| Self-harm scenarios flagged for a support response | 1 of 1 | |
| Score never decreased | 16 of 16 | |
| Stage 2 calls, used / made | 37 / 43 | |
| Messages where some analysis was unavailable | 0 | |
| Model calls per endpoint | {'wb_llama70b': 177, 'meta': 22, 'fw_muse': 21} | |
| Cost of priced calls (lower bound) | USD 0.3205 (0 calls unpriced) | |
| Wall time, concurrency 4 | 95 s | |

Latency per call:

| Purpose | p50 | p95 | n |
| --- | --- | --- | --- |
| stage1 | 420 ms | 571 ms | 177 |
| stage2 | 5562 ms | 8524 ms | 43 |

Confusion (rows expected, columns final):

| expected \ final | aman | perhatian | waspada | mendesak |
| --- | --- | --- | --- | --- |
| aman | 5 | 0 | 0 | 0 |
| perhatian | 0 | 4 | 2 | 0 |
| waspada | 0 | 1 | 2 | 1 |
| mendesak | 0 | 0 | 0 | 1 |

Per scenario:

| Scenario | Expected | Final | Starts | First raise | Scores |
| --- | --- | --- | --- | --- | --- |
| data_pribadi-002 | perhatian | waspada | 5 | 5 | 0 0 15 22 68 68 68 68 68 68 |
| data_pribadi-005 | perhatian | perhatian | 4 | 4 | 0 0 0 45 45 45 45 45 45 |
| kasus_sulit-004 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| kasus_sulit-008 | perhatian | waspada | 3 | 6 | 0 0 22 22 22 68 68 68 68 68 68 |
| kasus_sulit-009 | perhatian | perhatian | 3 | 5 | 0 0 12 12 30 30 30 30 30 30 |
| menyakiti_diri-001 | perhatian | perhatian | 3 | 3 | 0 0 48 48 48 58 58 58 58 58 58 |
| pendekatan_berisiko-001 | mendesak | mendesak | 5 | 7 | 0 0 0 0 20 20 42 42 68 68 88 88 90 90 |
| pendekatan_berisiko-002 | waspada | waspada | 5 | 7 | 0 0 0 0 28 28 38 38 62 62 68 68 68 |
| pendekatan_berisiko-008 | waspada | waspada | 7 | 9 | 0 0 0 0 0 0 18 18 42 42 68 68 68 68 |
| pendekatan_berisiko-012 | waspada | mendesak | 8 | 8 | 0 0 0 0 0 0 0 35 35 78 78 90 90 |
| perundungan-006 | perhatian | perhatian | 4 | 2 | 0 30 30 30 30 45 45 45 45 |
| perundungan-007 | waspada | perhatian | 2 | 4 | 0 0 0 30 30 30 30 30 30 30 35 |
| wajar-002 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-003 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| wajar-007 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-010 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
