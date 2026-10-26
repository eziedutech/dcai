# Digital Safe dcAI

Your AI companion for growing up safe in the digital world. dcAI guides children toward
healthy digital citizenship in the moment, and gives parents insight and conversation
starters instead of their child's conversations.

Status: prototype for the Meta Global AI Developer Hackathon (26 Oct to 4 Nov 2026),
built from a new repository during the event. Day 3 of 10.

Muse Spark is a reasoning model: it always thinks before answering, and the thinking tokens
count toward `max_tokens` and output cost. The client logs them separately, and a reply cut
by the token budget is reported as truncated rather than retried.

> All data in this repository, in tests and in the demo is synthetic. No real child data is
> used anywhere.

## What works today

| Part | State |
| --- | --- |
| `LLMClient` with `MuseClient` (Muse Spark) and `OpenWeightsClient` (small open-weights model) | Built and tested with mocked providers |
| Provider pool: rotation across hosts, failover on 429, timeout and 5xx, rest period from `Retry-After`, bounded retries | Built and tested |
| Schema-validated JSON output, one repair attempt, then a typed failure for the caller's safe fallback | Built and tested |
| Stage 2 risk assessment and Citizenship Coach output schemas | Built and tested |
| Test that fails if message text reaches a log | Built |
| A real call to a live model | Done: Muse Spark (`muse-spark-open` on Fireworks), structured JSON valid on the first attempt, 2.8 s, USD 0.0012 |
| Meta Model API endpoint | Supported by config, not called yet: no key |
| Llama for stage 1 | Llama 3.3 70B on W&B Inference, chosen over 3.1 8B by measurement on the dev split (below) |
| Guardian accounts: register, login, 15-minute access token, rotating refresh token (reuse ends all sessions), Argon2 passwords | Built and tested |
| Child profiles (nickname and age range, never a birth date) | Built and tested |
| Consent records: tied to a text version, append-only (a database trigger refuses UPDATE), withdrawal is a new record | Built and tested on SQLite and PostgreSQL |
| Delete all of a child's data, with an audit entry that keeps only the id | Built and tested |
| Authorization: a guardian only reaches their own children (another guardian's child answers 404) | Tested |
| 50 synthetic scenarios, 543 messages, six groups | Drafted, waiting for human review. Split 34 dev / 16 test, test set locked |
| Masking of personal data before any model call (phone, email, card, address, school, handle, names) | Built, rule-based, 55 shared test cases |
| Grooming Shield stage 1: per-message labels on masked text | Built, measured on the dev split |

### Stage 1 on the dev split (34 scenarios, 366 messages)

Measured against the dataset labels, which are still drafts. These are development numbers
that the prompt was tuned on, not the final evaluation; the test split stays untouched until
then.

| Model | Labelled messages found | Ordinary-chat messages given a label | p95 latency | Cost |
| --- | --- | --- | --- | --- |
| Llama 3.3 70B | recall 0.88, precision 0.77 | 4 of 80 | 1.5 s | USD 0.22 |
| Llama 3.1 8B | recall 0.86, precision 0.53 | 24 of 80 | 1.4 s | USD 0.07 |

Weakest labels for 70B: `pindah_kanal` (precision 0.43) and `membangun_kedekatan`
(precision 0.50). Full tables in `eval/stage1/`.

Not built yet: risk pipeline, coach, dashboard, keyboard, simulator, evaluation. This table
is updated as each part lands.

## Models

All model calls go through one interface, so the app never depends on one provider.

- Reasoning pool (stage 2 assessment, Citizenship Coach): Muse Spark, through the Meta Model
  API and other hosts that serve it. Model IDs are read from the environment, never written
  in code.
- Screening pool (stage 1 per-message labels): a small open-weights model.

Each pool can hold several endpoints. Calls rotate across them so no single provider carries
all the load. Costs are logged per call from configured prices; when a price is unknown the
log says `unknown` instead of guessing.

## Run

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14.

```bash
make setup
make test
make lint
make dev        # API on http://127.0.0.1:8000, GET /v1/health
```

Database tests run on SQLite, and also on PostgreSQL when `DCAI_TEST_PG_URL` points at a
throwaway database (`code/docker-compose.dev.yml` starts one; CI always runs both).
Migrations: `uv run alembic upgrade head` from `code/backpy`.

Configure models in `code/backpy/.env` (copy `.env.example`). Then:

```bash
make models P=fireworks F=muse   # list model IDs a provider serves
make probe                       # one small synthetic call per endpoint (costs credits)
```

Without `make` (for example on Windows), run the same commands from `code/backpy` with
`uv run ...`, as written in the `Makefile`.

## Privacy by design (what the code enforces today)

- Personal data is masked by deterministic rules before any model sees a message. The
  model receives markers such as `[TELEPON]`, never the value. Not recognised by these
  rules, and so not masked: names that are neither known to the system nor introduced
  ("namaku ..."), a class without a school, and places described in words ("deket
  minimarket yg biru").

- No table has a column for conversation text. A test inspects the migrated database and
  fails if a text-like column appears; the only binary column is the encrypted, expiring
  evidence excerpt reserved for the urgent level.

- Log lines from model calls carry metadata only: purpose, endpoint, model, tokens, latency,
  cost. A test sends a sentinel string through every success and failure path, including
  providers that echo the request in their error, and fails if it appears in any log.
- Provider error messages are reduced to error type and code before they reach an exception,
  because providers sometimes echo request content.
- Coach text cannot contain links or phone-like numbers: help channels will come from
  manually verified configuration, never from the model.

## Limitations

- The evaluation will use synthetic data written by the team, not real conversations, and
  has not been validated by child protection experts. Expert review and a consented pilot
  are the next steps.
- Every assessment is an estimate with a confidence level. AI can be wrong.

## Development notes

A Code Assistant was used to accelerate development and debugging.

## License

MIT, see [LICENSE](LICENSE).
