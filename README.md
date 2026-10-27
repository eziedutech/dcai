# Digital Safe dcAI

> An AI companion that helps children make safe choices online at the moment it matters, and gives parents insight and conversation starters instead of their child's conversations. When a chat starts to follow a risky pattern, the child gets a short, friendly reminder with the reason; the parent learns what kind of pattern appeared and how to talk about it, never what was written.

![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB)
![FastAPI 0.162](https://img.shields.io/badge/FastAPI-0.162-009688)
![Muse Spark 1.3](https://img.shields.io/badge/Muse%20Spark-1.3-0866FF)
![Llama 3.3 70B](https://img.shields.io/badge/Llama-3.3%2070B-0866FF)
![PostgreSQL 18](https://img.shields.io/badge/PostgreSQL-18-336791)

Built for the **Meta Global AI Developer Hackathon** (Cerebral Valley, 26 Oct to 4 Nov 2026). Prototype; all data is synthetic.

**Direction:** dcAI Guardian, an Android app a parent installs on the child's phone (ages 10 to 17), as a second layer next to Google Family Link: Family Link for limits, dcAI for understanding. Masking and a small classifier run on the phone; only flagged, masked messages reach the cloud. Decision record: [docs/proposals/0002-arah-c-dcai-guardian.md](docs/proposals/0002-arah-c-dcai-guardian.md).

## Table of Contents

- [What it is](#what-it-is)
- [How it works](#how-it-works)
- [How to test](#how-to-test)
- [Architecture](#architecture)
- [Running locally](#running-locally)
- [Configuration](#configuration)
- [Results](#results)
- [What it does not claim](#what-it-does-not-claim)
- [Credits and licenses](#credits-and-licenses)
- [How this was built](#how-this-was-built)
- [License](#license)

## What it is

Parental control apps either block or show parents everything. dcAI does neither: the child is guided first, and the parent receives a summary.

1. **Mask.** Names, phone numbers, emails, card numbers, addresses and schools are replaced by markers before any model sees a message.
2. **Label.** Llama labels each message with behaviour patterns: building closeness fast, asking for secrecy, moving to a private app, asking for personal data or photos, offering gifts, testing limits, pressure, bullying, distress.
3. **Assess.** When the recent messages show a signal, Muse Spark assesses the conversation window. A deterministic rule floor sits under the model: the score is the highest of the model, the rules and the previous score.
4. **Guide.** When the level rises, or a child first shows distress, the Citizenship Coach gives the child a nudge of at most two sentences, the parent insight with three conversation starters and what to do and avoid, and a one-minute lesson.

### Built today

- **One model interface** (`LLMClient`) over a pool of providers: Muse Spark on the Meta Model API and on Fireworks, Llama on W&B Inference. Calls rotate across providers, fail over on rate limits and outages, and every output is validated against a schema.
- **Masking by fixed rules**, with 55 shared test cases meant for the keyboard as well.
- **Grooming Shield**, stages 1 and 2, the rule floor, and `POST /v1/messages/analyze`, measured live on the dev split (below).
- **Citizenship Coach** on Muse Spark, with fixed templates for every situation, level and language when the model fails. Code rejects blame toward the child, punishment advice, links, phone-like numbers and mixed languages. Help channels come from `data/coach/channels.json`, where only manually verified entries carry a number.
- **Guardian accounts and consent.** Analysis runs only while consent is active. Consent records cannot be edited, only added to.
- **Delete all of a child's data** with one call. Paired phones are told and their tokens end.
- **Backend for the child's phone.** A parent creates a single-use pairing code; the phone trades it for a device token stored only as a hash. The phone reads its configuration (scopes it may use, age range, language), reports which protection services are on (a service switched off is an event for the parent), sends flagged messages, image labels (never pixels) and false detections the parent confirmed (stored without child or device id).
- **One queue per conversation.** The phone gets `202` in milliseconds; analysis runs in the background. Messages that arrive together share one stage 2 call and one Coach call, for the final level.
- **Live updates over SSE** with `Last-Event-ID` replay: the phone receives levels with a reviewed template nudge at once, then the model's nudge; the dashboard receives events, assessments and insight. Parent insight never goes to the phone.
- **50 synthetic scenarios** (543 messages, six groups), with a locked 34/16 dev/test split.

### Not built yet

In build order: parent dashboard (Next.js) with Ask dcAI, the Android app (Kotlin: accessibility text, on-phone masking, nudge overlay), a synthetic chat app and scenario player, visual protection, distillation to a smaller Llama, flagged domains, voice notes, the final evaluation.

## How it works

```
message ──> mask ──> stage 1: Llama 3.3 70B ──> rule floor ──┐
           (rules)   labels + signal per msg   (deterministic) ├─> score = max(previous, floor, model)
                                                               │
                     stage 2: Muse Spark  <── only if the ─────┘
                     window assessment        window shows a signal
```

- **The model may raise the level, never lower it below the rules.** For example, a stranger asking for personal data sets at least `waspada`, and secrecy plus a move to another app sets `mendesak`.
- **The score never drops within a conversation.** This is a deliberate, cautious choice, kept even after a restart.
- **If a model fails, the level is never shown as safe.** A stage 1 outage shows `perhatian` with "analysis unavailable".
- **Levels:** `aman` 0 to 29, `perhatian` 30 to 59, `waspada` 60 to 84, `mendesak` 85 to 100. Every assessment carries a confidence level and is marked as an estimate.

## How to test

```bash
cd code/backpy && uv sync && uv run pytest
```

Database tests also run on PostgreSQL when `DCAI_TEST_PG_URL` points at a throwaway database. `code/docker-compose.dev.yml` starts one, and CI always runs both.

Real model calls (these spend a little credit):

```bash
cd code/backpy
uv run python -m app.llm.probe call                    # one call per configured endpoint
uv run python -m app.risk.stage1_eval wb_llama70b      # stage 1 on the dev split
uv run python -m app.scenarios.validate                # check the scenario files
uv run python -m app.scenarios.split --check           # check the locked split
```

## Architecture

```
code/backpy/   FastAPI: llm (provider pool), privacy (masking), risk (stage 1, floor, stage 2,
               pipeline), coach, analysis (per-conversation queue), live (SSE broker), consent,
               auth, api (/v1, /v1/device), migrations (Alembic), tests
data/          scenarios (synthetic JSON, split.json), privacy (masking test cases)
eval/          measurement output (ids and labels only, no text)
docs/          ADRs and daily log
```

- **No column can hold conversation text.** A test inspects the migrated database. The conversation window lives in memory only.
- **Message text never reaches a log.** Every model call path is tested with a sentinel string, including providers that echo the request in their error.
- **Consent is append-only.** A database trigger refuses UPDATE on SQLite and PostgreSQL.
- **A guardian reaches only their own children.** Another guardian's child, conversation or device answers 404.
- **The phone knows only what the child may see:** its configuration, the level of its own conversations and nudges. A test checks responses and live updates for parent insight.
- **One process for live updates.** The SSE broker and the queues live in memory; several workers would need a shared bus (PostgreSQL LISTEN/NOTIFY).
- **Model IDs and prices come from the environment**, never from code.

## Running locally

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14. PostgreSQL 18 is optional; SQLite works for development.

```bash
cd code/backpy
cp .env.example .env            # add keys and SECRET_KEY
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000     # GET /v1/health
```

With `make` available, `make setup`, `make test`, `make lint` and `make dev` do the same.

## Configuration

| Variable | Purpose |
|---|---|
| `REASONING_ENDPOINTS`, `SCREENING_ENDPOINTS` | endpoint names in each pool; calls rotate across them |
| `META_API_KEY`, `META_API_BASE`, `MUSE_MODEL`, `META_REASONING_EFFORT` | Meta Model API endpoint `meta` (model ID from `GET /v1/models`) |
| `FIREWORKS_BASE`, `FIREWORKS_API_KEY`, `FW_MUSE_*` | Muse Spark on Fireworks |
| `WANDB_BASE`, `WANDB_API_KEY`, `WB_LLAMA70B_*`, `WB_LLAMA8B_*` | Llama on W&B Inference |
| `<NAME>_PRICE_IN_PER_MTOK`, `_CACHED_`, `_OUT_` | prices for cost logs; without them the cost is logged as `unknown` |
| `<NAME>_JSON_MODE`, `<NAME>_REASONING_EFFORT` | per endpoint: `json_schema`, `json_object` or `none`; reasoning effort |
| `DATABASE_URL` | SQLite or PostgreSQL |
| `SECRET_KEY` | signs 15-minute access tokens; refresh tokens rotate |
| `PAIRING_CODE_MINUTES`, `DEVICE_MESSAGES_PER_MINUTE` | pairing code lifetime; per-phone message limit |
| `SSE_HEARTBEAT_SECONDS`, `SSE_MAX_SECONDS` | stream heartbeat; streams close after this and clients reconnect |

`.env.example` lists every variable.

## Results

### Tests

| Suite | Result |
|---|---|
| Unit and API tests on SQLite | 286 passed |
| The database tests again on PostgreSQL 18 | 59 passed |

### Full pipeline on the dev split

34 synthetic scenarios played message by message: Llama 3.3 70B for stage 1, Muse Spark on the Meta Model API and Fireworks for stage 2, and the rule floor. Expected levels are dataset drafts. These are development numbers; the test split is kept for the final evaluation.

| Measure | Result | Spec target |
|---|---|---|
| Risky approaches reaching `waspada` or higher | 8 of 8 | at least 0.9 |
| Ordinary chats and hard cases reaching `waspada` or higher | 0 of 14 | at most 0.1 |
| Detection delay, median | 0 messages (n=19) | at most 2 |
| Final level exactly as expected | 28 of 34 | |
| Self-harm scenarios flagged for a support response | 3 of 3 | |
| Messages without a complete analysis | 0 of 366 | |
| Stage 2 latency per call | p50 6.1 s, p95 15.3 s | p95 under 5 s per message |

- **Stage 2 latency misses the target.** It runs only on messages that bring new evidence (96 of 366), but each of those calls takes several seconds. The phone path therefore no longer waits for it: see the next section.
- **One bullying case is missed.** Exclusion from a class group (`perundungan-001`) stays `aman`.
- **Two ordinary chats end at `perhatian`.** One is a teacher asking for a parent's phone number, where the child's reply sets the personal data rule.
- A first run with a 1500-token cap for stage 2 had 52 of 208 calls cut while the model was still reasoning. The cap is now 3000.

Full tables are in `eval/pipeline/dev.md`.

### Phone path, one live run

Four synthetic messages from a stranger in a game chat, sent at once through `/v1/device/messages`, live models, one run (not a benchmark):

| Moment | Time after the first message |
|---|---|
| Each message accepted (`202`) | 10 to 21 ms |
| Level `perhatian` with a template nudge on the phone stream | 2.0 s |
| Level `mendesak` with a template nudge | 5.9 s |
| The model's nudge for `mendesak` | 15.6 s |

Model calls: 4 stage 1, 1 stage 2, 1 Coach. Before the queue merged them, the same run made 2 Coach calls and reached `mendesak` later, because a Coach for the out-of-date `perhatian` level held the queue.

### Citizenship Coach

9 cases covering every situation (approach, child bullied, child bullying, shared data, distress, general) at `perhatian`, `waspada` and `mendesak`, in Indonesian and English. All 9 were answered by the model and passed the schema and tone rules. Latency was 4 to 8 s on the Meta Model API and 18 to 27 s on Fireworks. The tone review by a person (spec rubric, target 4 of 5) is pending.

Found and fixed on the way: Fireworks timed out at 20 s on every coach call (the coach now gets 45 s); English output mixed in Indonesian words (now rejected and replaced by a template); and Indonesian reduplication lost its hyphen ("hati hati", now repaired in code).

### Stage 1 on the dev split

34 synthetic scenarios, 366 messages, scored against the dataset labels (drafts, not yet reviewed by a person). The prompt was tuned on this split, so these are development numbers. The 16 test scenarios stay untouched until the final evaluation.

| Model | Labelled messages found | Ordinary-chat messages given a label | p95 latency | Cost per run |
|---|---|---|---|---|
| **Llama 3.3 70B (used)** | recall 0.88, precision 0.77 | 4 of 80 | 1.5 s | USD 0.22 |
| Llama 3.1 8B | recall 0.86, precision 0.53 | 24 of 80 | 1.4 s | USD 0.07 |

The weakest labels for 70B are `pindah_kanal` (precision 0.43) and `membangun_kedekatan` (0.50). Full tables are in `eval/stage1/`.

### Masking

On all 543 scenario messages, 15 of the 17 child messages that share personal data are caught, and 0 of the 121 ordinary-chat messages. The rules were adjusted after seeing these messages, so this is not a clean test. The final precision and recall will be measured on unseen cases.

## What it does not claim

- **It is not tested with real children or families**, and it has not been reviewed by child-protection experts. The evaluation uses synthetic scenarios written for this project. Expert review and a consented pilot come next.
- **Every assessment is an estimate and can be wrong.** The interface says so.
- **Masking does not catch everything.** It misses names the system does not know and that are not introduced with a phrase such as "namaku", a class without a school, and places described in words ("near the blue shop").
- **Free Meta credits allow Meta to use request content for product improvement.** Only synthetic data is sent. Real use needs the `meta` endpoint removed or paid usage.
- **Not everything is processed on the device.** Masked messages go to model providers.
- The consent text has not had legal review.

## Credits and licenses

- **Meta Muse Spark** through the Meta Model API and Fireworks; **Meta Llama 3.3 70B and 3.1 8B** through W&B Inference (Llama 3.x Community License).
- **FastAPI**, **uvicorn**, **pydantic**, **httpx**, **SQLAlchemy**, **Alembic**, **psycopg**, **argon2-cffi**, **PyJWT**, **pytest**, **respx**, **ruff**, **PostgreSQL**: their respective open source licenses.

## How this was built

A Code Assistant was used to accelerate development and debugging. Design decisions, measurements and claims were checked against real runs. The daily log is in `docs/log/`.

## License

MIT, see [LICENSE](LICENSE).
