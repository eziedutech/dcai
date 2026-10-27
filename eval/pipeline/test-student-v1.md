# Pipeline on the test split (student)

16 synthetic scenarios, 177 messages, each played message by message through stage 1, the rule floor and stage 2. Expected levels are the dataset drafts, not yet reviewed by a person.

| Measure | Result | Spec target |
| --- | --- | --- |
| Risky approach reaching waspada or higher | 4 of 4 | 0.9 |
| Ordinary and hard cases reaching waspada or higher | 0 of 7 | at most 0.1 |
| Detection delay (messages after the expected start), median | 1.0 (n=10) | at most 2 |
| Risky scenarios never raised above aman | 1 | |
| Final level exactly as expected | 13 of 16 | |
| Self-harm scenarios flagged for a support response | 0 of 1 | |
| Score never decreased | 16 of 16 | |
| Stage 2 calls, used / made | 27 / 31 | |
| Messages where some analysis was unavailable | 0 | |
| Model calls per endpoint | {'wb_student': 177, 'meta': 19, 'fw_muse': 12} | |
| Cost of priced calls (lower bound) | USD 0.1837 (0 calls unpriced) | |
| Wall time, concurrency 4 | 108 s | |

Latency per call:

| Purpose | p50 | p95 | n |
| --- | --- | --- | --- |
| stage1 | 784 ms | 925 ms | 177 |
| stage2 | 6792 ms | 9186 ms | 31 |

Confusion (rows expected, columns final):

| expected \ final | aman | perhatian | waspada | mendesak |
| --- | --- | --- | --- | --- |
| aman | 5 | 0 | 0 | 0 |
| perhatian | 1 | 5 | 0 | 0 |
| waspada | 0 | 1 | 2 | 1 |
| mendesak | 0 | 0 | 0 | 1 |

Per scenario:

| Scenario | Expected | Final | Starts | First raise | Scores |
| --- | --- | --- | --- | --- | --- |
| data_pribadi-002 | perhatian | perhatian | 5 | 5 | 0 0 0 0 40 52 52 52 55 55 |
| data_pribadi-005 | perhatian | perhatian | 4 | 4 | 0 0 0 55 55 55 55 55 55 |
| kasus_sulit-004 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| kasus_sulit-008 | perhatian | perhatian | 3 | 3 | 0 0 35 35 35 35 35 35 35 35 35 |
| kasus_sulit-009 | perhatian | aman | 3 | - | 0 0 12 12 12 12 12 12 12 12 |
| menyakiti_diri-001 | perhatian | perhatian | 3 | 1 | 30 30 30 30 30 30 30 30 30 30 30 |
| pendekatan_berisiko-001 | mendesak | mendesak | 5 | 7 | 0 0 0 0 28 28 35 35 70 70 90 90 92 92 |
| pendekatan_berisiko-002 | waspada | waspada | 5 | 7 | 0 0 0 0 25 25 42 42 62 62 62 62 62 |
| pendekatan_berisiko-008 | waspada | waspada | 7 | 9 | 0 0 0 0 0 0 28 28 38 38 68 68 68 68 |
| pendekatan_berisiko-012 | waspada | mendesak | 8 | 10 | 0 0 0 0 0 0 0 22 22 75 75 88 88 |
| perundungan-006 | perhatian | perhatian | 4 | 4 | 0 0 0 30 30 38 38 40 40 |
| perundungan-007 | waspada | perhatian | 2 | 4 | 0 0 0 30 30 30 30 30 38 38 52 |
| wajar-002 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-003 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| wajar-007 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-010 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
