# Pipeline on the dev split

34 synthetic scenarios, 366 messages, each played message by message through stage 1, the rule floor and stage 2. Expected levels are the dataset drafts, not yet reviewed by a person.

| Measure | Result | Spec target |
| --- | --- | --- |
| Risky approach reaching waspada or higher | 8 of 8 | 0.9 |
| Ordinary and hard cases reaching waspada or higher | 0 of 14 | at most 0.1 |
| Detection delay (messages after the expected start), median | 0 (n=19) | at most 2 |
| Risky scenarios never raised above aman | 1 | |
| Final level exactly as expected | 28 of 34 | |
| Self-harm scenarios flagged for a support response | 3 of 3 | |
| Score never decreased | 34 of 34 | |
| Stage 2 calls, used / made | 82 / 96 | |
| Messages where some analysis was unavailable | 0 | |
| Model calls per endpoint | {'wb_llama70b': 366, 'meta': 50, 'fw_muse': 46} | |
| Cost of priced calls (lower bound) | USD 0.3566 (50 calls unpriced) | |
| Wall time, concurrency 4 | 255 s | |

Latency per call:

| Purpose | p50 | p95 | n |
| --- | --- | --- | --- |
| stage1 | 419 ms | 544 ms | 366 |
| stage2 | 6108 ms | 15289 ms | 96 |

Confusion (rows expected, columns final):

| expected \ final | aman | perhatian | waspada | mendesak |
| --- | --- | --- | --- | --- |
| aman | 12 | 2 | 0 | 0 |
| perhatian | 1 | 5 | 1 | 0 |
| waspada | 0 | 0 | 7 | 2 |
| mendesak | 0 | 0 | 0 | 4 |

Per scenario:

| Scenario | Expected | Final | Starts | First raise | Scores |
| --- | --- | --- | --- | --- | --- |
| data_pribadi-001 | perhatian | perhatian | 4 | 4 | 0 0 18 32 32 35 35 35 35 |
| data_pribadi-003 | perhatian | perhatian | 4 | 4 | 0 0 0 30 30 30 35 35 35 |
| data_pribadi-004 | perhatian | perhatian | 4 | 3 | 0 0 32 55 55 55 55 55 55 |
| data_pribadi-006 | perhatian | perhatian | 4 | 4 | 0 0 15 30 30 30 30 30 30 |
| kasus_sulit-001 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| kasus_sulit-002 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| kasus_sulit-003 | aman | perhatian | - | 4 | 0 0 15 30 30 30 30 30 30 30 |
| kasus_sulit-005 | aman | aman | - | - | 0 0 12 12 12 12 12 12 12 12 12 |
| kasus_sulit-006 | aman | aman | - | - | 0 0 10 10 10 10 10 10 10 10 |
| kasus_sulit-007 | aman | aman | - | - | 0 0 10 10 10 10 10 10 10 10 |
| menyakiti_diri-002 | waspada | waspada | 2 | 4 | 0 0 0 45 55 55 78 78 78 78 78 78 |
| menyakiti_diri-003 | perhatian | waspada | 3 | 3 | 0 0 78 78 78 78 78 78 78 78 |
| menyakiti_diri-004 | waspada | mendesak | 3 | 3 | 0 0 45 45 82 82 88 88 88 88 88 |
| pendekatan_berisiko-003 | mendesak | mendesak | 4 | 4 | 0 0 0 35 35 35 35 72 72 90 90 90 90 92 |
| pendekatan_berisiko-004 | waspada | waspada | 6 | 6 | 0 0 0 0 0 35 35 48 48 75 75 75 75 |
| pendekatan_berisiko-005 | waspada | waspada | 5 | 7 | 0 0 0 0 20 20 40 40 65 65 72 72 |
| pendekatan_berisiko-006 | mendesak | mendesak | 3 | 3 | 0 0 32 32 32 68 68 88 88 90 90 92 92 |
| pendekatan_berisiko-007 | waspada | waspada | 6 | 8 | 0 0 0 0 0 22 22 62 62 68 68 74 74 |
| pendekatan_berisiko-009 | mendesak | mendesak | 5 | 7 | 0 0 0 0 18 18 78 78 78 78 88 88 92 92 |
| pendekatan_berisiko-010 | waspada | waspada | 4 | 4 | 0 0 0 35 35 45 45 78 78 78 78 78 |
| pendekatan_berisiko-011 | mendesak | mendesak | 6 | 6 | 0 0 0 0 0 32 32 42 42 72 72 88 88 92 |
| perundungan-001 | perhatian | aman | 4 | - | 0 0 0 0 0 0 0 0 0 |
| perundungan-002 | waspada | waspada | 3 | 5 | 0 0 15 15 38 62 62 62 72 72 72 |
| perundungan-003 | perhatian | perhatian | 3 | 3 | 0 0 35 35 38 38 38 38 38 |
| perundungan-004 | waspada | waspada | 3 | 3 | 0 0 30 38 42 42 58 58 58 72 72 |
| perundungan-005 | waspada | mendesak | 4 | 1 | 35 35 35 68 68 86 88 88 88 88 |
| wajar-001 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 0 |
| wajar-004 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-005 | aman | perhatian | - | 2 | 0 30 30 30 30 30 30 30 30 30 |
| wajar-006 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 |
| wajar-008 | aman | aman | - | - | 0 0 0 0 0 0 15 15 15 15 |
| wajar-009 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-011 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
| wajar-012 | aman | aman | - | - | 0 0 0 0 0 0 0 0 0 0 |
