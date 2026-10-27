# Pipeline on the test split (student-v2)

16 synthetic scenarios, 177 messages, each played message by message through stage 1, the rule floor and stage 2. Expected levels are the dataset drafts, not yet reviewed by a person.

| Measure | Result | Spec target |
| --- | --- | --- |
| Risky approach reaching waspada or higher | 4 of 4 | 0.9 |
| Ordinary and hard cases reaching waspada or higher | 1 of 7 | at most 0.1 |
| Detection delay (messages after the expected start), median | 0.0 (n=10) | at most 2 |
| Risky scenarios never raised above aman | 1 | |
| Final level exactly as expected | 12 of 16 | |
| Self-harm scenarios flagged for a support response | 1 of 1 | |
| Score never decreased | 16 of 16 | |
| Stage 2 calls, used / made | 32 / 33 | |
| Messages where some analysis was unavailable | 0 | |
| Model calls per endpoint | {'wb_student': 177, 'meta': 17, 'fw_muse': 16} | |
| Cost of priced calls (lower bound) | USD 0.1720 (0 calls unpriced) | |
| Wall time, concurrency 4 | 130 s | |

Latency per call:

| Purpose | p50 | p95 | n |
| --- | --- | --- | --- |
| stage1 | 458 ms | 853 ms | 177 |
| stage2 | 8903 ms | 12955 ms | 33 |

Confusion (rows expected, columns final):

| expected \ final | aman | perhatian | waspada | mendesak |
| --- | --- | --- | --- | --- |
| aman | 5 | 0 | 0 | 0 |
| perhatian | 1 | 3 | 2 | 0 |
| waspada | 0 | 1 | 3 | 0 |
| mendesak | 0 | 0 | 0 | 1 |

Per scenario:

| Scenario | Expected | Final | Starts | First raise | Scores |
| --- | --- | --- | --- | --- | --- |
| data_pribadi-002 | perhatian | waspada | 5 | 5 | 0 0 0 18 78 78 78 78 78 78 |
| data_pribadi-005 | perhatian | perhatian | 4 | 4 | 0 0 0 42 42 42 42 42 42 |
| kasus_sulit-004 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| kasus_sulit-008 | perhatian | waspada | 3 | 6 | 0 0 20 20 20 68 68 68 68 68 68 |
| kasus_sulit-009 | perhatian | aman | 3 | - | 0 0 12 12 12 12 12 12 12 12 |
| menyakiti_diri-001 | perhatian | perhatian | 3 | 1 | 30 30 30 30 30 38 38 38 38 38 38 |
| pendekatan_berisiko-001 | mendesak | mendesak | 5 | 5 | 0 0 0 0 32 32 42 42 68 68 88 88 92 92 |
| pendekatan_berisiko-002 | waspada | waspada | 5 | 5 | 0 0 0 0 35 35 48 48 68 68 72 72 72 |
| pendekatan_berisiko-008 | waspada | waspada | 7 | 9 | 0 0 0 0 0 0 25 25 45 45 68 68 72 72 |
| pendekatan_berisiko-012 | waspada | waspada | 8 | 8 | 0 0 0 0 0 0 0 42 42 78 78 82 82 |
| perundungan-006 | perhatian | perhatian | 4 | 4 | 0 0 0 32 32 38 38 42 42 |
| perundungan-007 | waspada | perhatian | 2 | 4 | 0 0 0 30 30 30 30 30 30 30 35 |
| wajar-002 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-003 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| wajar-007 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-010 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
