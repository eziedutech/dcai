# Pipeline on the test split (pool-bt)

18 synthetic scenarios, 197 messages, each played message by message through stage 1, the rule floor and stage 2. Expected levels are the dataset drafts, not yet reviewed by a person.

| Measure | Result | Spec target |
| --- | --- | --- |
| Risky approach reaching waspada or higher | 4 of 4 | 0.9 |
| Ordinary and hard cases reaching waspada or higher | 1 of 7 | at most 0.1 |
| Detection delay (messages after the expected start), median | 0.0 (n=12) | at most 2 |
| Risky scenarios never raised above aman | 1 | |
| Final level exactly as expected | 13 of 18 | |
| Self-harm scenarios flagged for a support response | 1 of 1 | |
| Score never decreased | 18 of 18 | |
| Stage 2 calls, used / made | 37 / 40 | |
| Messages where some analysis was unavailable | 0 | |
| Model calls per endpoint | {'wb_student': 197, 'meta': 14, 'bt_muse': 14, 'fw_muse': 12} | |
| Cost of priced calls (lower bound) | USD 0.1678 (14 calls unpriced) | |
| Wall time, concurrency 4 | 98 s | |

Latency per call:

| Purpose | p50 | p95 | n |
| --- | --- | --- | --- |
| stage1 | 768 ms | 924 ms | 197 |
| stage2 | 4991 ms | 10043 ms | 40 |

Confusion (rows expected, columns final):

| expected \ final | aman | perhatian | waspada | mendesak |
| --- | --- | --- | --- | --- |
| aman | 5 | 0 | 0 | 0 |
| perhatian | 1 | 3 | 2 | 0 |
| waspada | 0 | 1 | 4 | 1 |
| mendesak | 0 | 0 | 0 | 1 |

Per scenario:

| Scenario | Expected | Final | Starts | First raise | Scores |
| --- | --- | --- | --- | --- | --- |
| data_pribadi-002 | perhatian | waspada | 5 | 5 | 0 0 0 24 68 78 78 78 78 78 |
| data_pribadi-005 | perhatian | perhatian | 4 | 4 | 0 0 0 35 35 35 42 42 42 |
| kasus_sulit-004 | aman | aman | - | - | 0 0 12 12 12 12 12 12 12 12 12 |
| kasus_sulit-008 | perhatian | waspada | 3 | 3 | 0 0 35 35 35 72 72 72 72 72 72 |
| kasus_sulit-009 | perhatian | aman | 3 | - | 0 0 12 12 12 12 12 12 12 12 |
| kenakalan-005 | waspada | waspada | 3 | 3 | 0 0 68 68 72 72 74 74 75 75 |
| kenakalan-006 | waspada | mendesak | 3 | 1 | 30 30 42 42 72 72 87 87 88 88 |
| menyakiti_diri-001 | perhatian | perhatian | 3 | 3 | 0 0 38 38 38 45 45 45 45 45 45 |
| pendekatan_berisiko-001 | mendesak | mendesak | 5 | 7 | 0 0 0 0 25 25 38 38 68 68 87 87 90 90 |
| pendekatan_berisiko-002 | waspada | waspada | 5 | 5 | 0 0 0 0 35 35 42 42 62 62 72 72 72 |
| pendekatan_berisiko-008 | waspada | waspada | 7 | 7 | 0 0 0 0 0 0 32 32 68 68 72 72 78 78 |
| pendekatan_berisiko-012 | waspada | waspada | 8 | 10 | 0 0 0 0 0 0 0 28 28 78 78 78 78 |
| perundungan-006 | perhatian | perhatian | 4 | 4 | 0 0 0 30 30 38 38 38 38 |
| perundungan-007 | waspada | perhatian | 2 | 4 | 0 0 0 30 30 30 30 30 35 35 35 |
| wajar-002 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-003 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| wajar-007 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-010 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
