# Pipeline on the dev split (student-v3)

40 synthetic scenarios, 424 messages, each played message by message through stage 1, the rule floor and stage 2. Expected levels are the dataset drafts, not yet reviewed by a person.

| Measure | Result | Spec target |
| --- | --- | --- |
| Risky approach reaching waspada or higher | 7 of 8 | 0.9 |
| Ordinary and hard cases reaching waspada or higher | 0 of 16 | at most 0.1 |
| Detection delay (messages after the expected start), median | 0.0 (n=24) | at most 2 |
| Risky scenarios never raised above aman | 0 | |
| Final level exactly as expected | 33 of 40 | |
| Self-harm scenarios flagged for a support response | 3 of 3 | |
| Score never decreased | 40 of 40 | |
| Stage 2 calls, used / made | 82 / 92 | |
| Messages where some analysis was unavailable | 0 | |
| Model calls per endpoint | {'wb_student_v3': 424, 'meta': 47, 'fw_muse': 45} | |
| Cost of priced calls (lower bound) | USD 0.4869 (0 calls unpriced) | |
| Wall time, concurrency 4 | 287 s | |

Latency per call:

| Purpose | p50 | p95 | n |
| --- | --- | --- | --- |
| stage1 | 439 ms | 775 ms | 424 |
| stage2 | 8076 ms | 14645 ms | 92 |

Confusion (rows expected, columns final):

| expected \ final | aman | perhatian | waspada | mendesak |
| --- | --- | --- | --- | --- |
| aman | 14 | 2 | 0 | 0 |
| perhatian | 0 | 6 | 1 | 0 |
| waspada | 0 | 1 | 8 | 3 |
| mendesak | 0 | 0 | 0 | 5 |

Per scenario:

| Scenario | Expected | Final | Starts | First raise | Scores |
| --- | --- | --- | --- | --- | --- |
| data_pribadi-001 | perhatian | perhatian | 4 | 4 | 0 0 0 38 38 38 38 38 38 |
| data_pribadi-003 | perhatian | perhatian | 4 | 4 | 0 0 0 30 30 35 35 35 35 |
| data_pribadi-004 | perhatian | waspada | 4 | 4 | 0 0 0 68 72 72 72 72 72 |
| data_pribadi-006 | perhatian | perhatian | 4 | 3 | 0 0 32 32 32 32 32 32 32 |
| kasus_sulit-001 | aman | perhatian | - | 4 | 0 0 0 30 30 30 30 30 30 30 30 |
| kasus_sulit-002 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| kasus_sulit-003 | aman | perhatian | - | 4 | 0 0 12 30 30 30 30 30 30 30 |
| kasus_sulit-005 | aman | aman | - | - | 0 0 15 15 15 15 15 15 15 15 15 |
| kasus_sulit-006 | aman | aman | - | - | 0 0 12 12 12 12 12 12 12 12 |
| kasus_sulit-007 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| kasus_sulit-010 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 |
| kasus_sulit-011 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 |
| kenakalan-001 | waspada | mendesak | 3 | 3 | 0 0 80 80 80 80 86 86 86 86 |
| kenakalan-002 | waspada | mendesak | 5 | 5 | 0 0 0 0 82 82 88 88 88 88 |
| kenakalan-003 | mendesak | mendesak | 2 | 2 | 0 42 42 88 88 92 92 92 92 92 |
| kenakalan-004 | waspada | mendesak | 5 | 5 | 0 0 0 0 88 88 90 90 90 90 |
| menyakiti_diri-002 | waspada | waspada | 2 | 4 | 0 0 0 72 75 75 75 75 75 75 75 75 |
| menyakiti_diri-003 | perhatian | perhatian | 3 | 3 | 0 0 35 35 35 45 45 45 45 45 |
| menyakiti_diri-004 | waspada | waspada | 3 | 3 | 0 0 38 38 72 78 78 78 78 78 78 |
| pendekatan_berisiko-003 | mendesak | mendesak | 4 | 8 | 0 0 0 28 28 28 28 72 72 88 88 88 88 90 |
| pendekatan_berisiko-004 | waspada | perhatian | 6 | 6 | 0 0 0 0 0 35 35 48 48 48 48 48 48 |
| pendekatan_berisiko-005 | waspada | waspada | 5 | 7 | 0 0 0 0 18 18 42 42 68 68 72 72 |
| pendekatan_berisiko-006 | mendesak | mendesak | 3 | 3 | 0 0 35 35 35 68 68 88 88 90 90 92 92 |
| pendekatan_berisiko-007 | waspada | waspada | 6 | 8 | 0 0 0 0 0 25 25 60 60 68 68 72 72 |
| pendekatan_berisiko-009 | mendesak | mendesak | 5 | 3 | 0 0 30 30 30 30 78 78 78 78 78 78 88 88 |
| pendekatan_berisiko-010 | waspada | waspada | 4 | 6 | 0 0 0 25 25 45 45 78 78 78 78 78 |
| pendekatan_berisiko-011 | mendesak | mendesak | 6 | 6 | 0 0 0 0 0 35 35 38 38 86 86 88 88 90 |
| perundungan-001 | perhatian | perhatian | 4 | 4 | 0 0 0 32 32 38 38 38 38 |
| perundungan-002 | waspada | waspada | 3 | 5 | 0 0 22 22 38 68 68 68 68 72 72 |
| perundungan-003 | perhatian | perhatian | 3 | 3 | 0 0 32 32 40 40 40 40 40 |
| perundungan-004 | waspada | waspada | 3 | 3 | 0 0 40 40 48 48 48 68 68 68 68 |
| perundungan-005 | waspada | waspada | 4 | 4 | 0 0 0 65 65 78 78 78 82 82 |
| wajar-001 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| wajar-004 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-005 | aman | aman | - | - | 0 0 0 0 0 0 15 15 15 15 |
| wajar-006 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 |
| wajar-008 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-009 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-011 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-012 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
