# Pipeline on the test split (student-v3)

18 synthetic scenarios, 197 messages, each played message by message through stage 1, the rule floor and stage 2. Expected levels are the dataset drafts, not yet reviewed by a person.

| Measure | Result | Spec target |
| --- | --- | --- |
| Risky approach reaching waspada or higher | 4 of 4 | 0.9 |
| Ordinary and hard cases reaching waspada or higher | 1 of 7 | at most 0.1 |
| Detection delay (messages after the expected start), median | 0.0 (n=12) | at most 2 |
| Risky scenarios never raised above aman | 1 | |
| Final level exactly as expected | 11 of 18 | |
| Self-harm scenarios flagged for a support response | 1 of 1 | |
| Score never decreased | 18 of 18 | |
| Stage 2 calls, used / made | 37 / 40 | |
| Messages where some analysis was unavailable | 0 | |
| Model calls per endpoint | {'wb_student_v3': 197, 'meta': 20, 'fw_muse': 20} | |
| Cost of priced calls (lower bound) | USD 0.2256 (0 calls unpriced) | |
| Wall time, concurrency 4 | 125 s | |

Latency per call:

| Purpose | p50 | p95 | n |
| --- | --- | --- | --- |
| stage1 | 425 ms | 620 ms | 197 |
| stage2 | 9322 ms | 16000 ms | 40 |

Confusion (rows expected, columns final):

| expected \ final | aman | perhatian | waspada | mendesak |
| --- | --- | --- | --- | --- |
| aman | 5 | 0 | 0 | 0 |
| perhatian | 1 | 2 | 3 | 0 |
| waspada | 0 | 1 | 3 | 2 |
| mendesak | 0 | 0 | 0 | 1 |

Per scenario:

| Scenario | Expected | Final | Starts | First raise | Scores |
| --- | --- | --- | --- | --- | --- |
| data_pribadi-002 | perhatian | waspada | 5 | 5 | 0 0 0 18 50 75 75 75 75 75 |
| data_pribadi-005 | perhatian | perhatian | 4 | 4 | 0 0 0 45 45 45 45 45 45 |
| kasus_sulit-004 | aman | aman | - | - | 0 0 18 18 18 18 18 18 18 18 18 |
| kasus_sulit-008 | perhatian | waspada | 3 | 6 | 0 0 22 22 22 62 62 62 62 62 62 |
| kasus_sulit-009 | perhatian | aman | 3 | - | 0 0 12 12 12 12 12 12 12 12 |
| kenakalan-005 | waspada | mendesak | 3 | 3 | 0 0 80 80 80 80 82 82 87 87 |
| kenakalan-006 | waspada | mendesak | 3 | 1 | 30 30 38 38 72 72 88 88 88 88 |
| menyakiti_diri-001 | perhatian | waspada | 3 | 3 | 0 0 45 45 45 72 72 72 72 72 72 |
| pendekatan_berisiko-001 | mendesak | mendesak | 5 | 7 | 0 0 0 0 28 28 48 48 72 72 88 88 90 90 |
| pendekatan_berisiko-002 | waspada | waspada | 5 | 5 | 0 0 0 0 35 35 38 38 68 68 68 68 68 |
| pendekatan_berisiko-008 | waspada | waspada | 7 | 9 | 0 0 0 0 0 0 20 20 38 38 72 72 72 72 |
| pendekatan_berisiko-012 | waspada | waspada | 8 | 8 | 0 0 0 0 0 0 0 35 35 78 78 78 78 |
| perundungan-006 | perhatian | perhatian | 4 | 4 | 0 0 0 30 30 42 42 42 42 |
| perundungan-007 | waspada | perhatian | 2 | 4 | 0 0 0 30 30 30 30 30 30 30 38 |
| wajar-002 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-003 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| wajar-007 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-010 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
