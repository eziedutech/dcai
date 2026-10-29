# dcAI: Digital Citizenship AI, Family Safety Guardian

> An AI companion that helps children make safe choices online at the moment it matters, and gives parents insight and conversation starters. When a chat starts to follow a risky pattern, the child gets a short, friendly reminder with the reason; the parent learns what kind of pattern appeared and how to talk about it. Message text is never shared.

![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB)
![FastAPI 0.162](https://img.shields.io/badge/FastAPI-0.162-009688)
![Muse Spark 1.3](https://img.shields.io/badge/Muse%20Spark-1.3-0866FF)
![Llama 3.3 70B](https://img.shields.io/badge/Llama-3.3%2070B-0866FF)
![PostgreSQL 18](https://img.shields.io/badge/PostgreSQL-18-336791)
![Next.js 16](https://img.shields.io/badge/Next.js-16-000000)
![Android API 30+](https://img.shields.io/badge/Android-API%2030%2B-3DDC84)

Built for the **Meta Global AI Developer Hackathon** (Cerebral Valley, 26 Oct to 4 Nov 2026). Prototype; all data is synthetic.

**Live:** [dcai.digitalsafe.app](https://dcai.digitalsafe.app) (homepage and parent dashboard; the phone's API is under `/v1`). Please use synthetic data only: free model credits allow the provider to use request content.

**Direction:** dcAI, an Android app a parent installs on the child's phone (ages 10 to 17): safety in chats, images and sites, healthy habits (daily time online, bedtime, breaks from endless short video), and guidance for the parent. It is one pillar of digitalsafe.app. Masking and a small classifier run on the phone; only flagged, masked messages reach the cloud.

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
- [About digitalsafe.app](#about-digitalsafeapp)
- [License](#license)

## What it is

Parental control apps tend to either block or show parents everything. dcAI guides the child first, then gives the parent a summary.

1. **Mask.** Names, phone numbers, emails, card numbers, addresses and schools are replaced by markers before any model sees a message.
2. **Label.** Llama labels each message with behaviour patterns: building closeness fast, asking for secrecy, moving to a private app, asking for personal data or photos, offering gifts, testing limits, pressure, bullying, invitations to fights, drugs, alcohol or weapons, distress.
3. **Assess.** When the recent messages show a signal, Muse Spark assesses the conversation window. A deterministic rule floor sits under the model: the score is the highest of the model, the rules and the previous score.
4. **Guide.** When the level rises, or a child first shows distress, the Citizenship Guide gives the child a nudge of at most two sentences, the parent insight with three conversation starters and what to do and avoid, and a one-minute lesson.

### Built today

- **One model interface** (`LLMClient`) over a pool of providers: Muse Spark on the Meta Model API and on Fireworks, Llama on an open-weights inference provider. Calls rotate across providers, fail over on rate limits and outages, and every output is validated against a schema.
- **Masking by fixed rules**, with 55 shared test cases meant for the keyboard as well.
- **Grooming Shield**, stages 1 and 2, the rule floor, and `POST /v1/messages/analyze`, measured live on the dev split (below).
- **Citizenship Guide** on Muse Spark, with fixed templates for every situation, level and language when the model fails. Code rejects blame toward the child, punishment advice, links, phone-like numbers and mixed languages. Help channels come from `data/guide/channels.json`, where only manually verified entries carry a number.
- **Distilled stage 1 student.** Muse Spark labels the dev messages; Llama 3.1 8B is fine-tuned on them with LoRA SFT on a serverless training service (OpenPipe ART), on exactly the production prompt. On the locked test split the full pipeline with the student matches 70B screening on every safety measure at 46% lower cost. v2 is the default stage 1 screener. Student v3, retrained with the invitation label, was evaluated and not adopted: it removes a false alarm but misses more risk (below). Details in `eval/distill/report.md`.
- **Guardian accounts and consent.** Analysis runs only while consent is active. Consent records cannot be edited, only added to.
- **Delete all of a child's data** with one call. Paired phones are told and their tokens end.
- **dcAI, the Android app** (Kotlin, API 30+). A parent pairs the child's phone with a code; the device token is stored on the phone, never shown again. A foreground service keeps a persistent notification the whole time dcAI is active (the transparency requirement and Google Play's monitoring-app rule, `isMonitoringTool=child_monitoring`), follows the live stream, and shows the child a nudge. Two ingest sources share one on-phone masking path: the dcAI keyboard checks the child's own typing, and an app that integrated the dcAI SDK (the included sample chat app, Messenger Z) hands over messages through a signature-permission broadcast. Masking is ported from Python and passes the same shared cases, so the phone and the server agree on what is personal.
- **Voice notes.** In a chat that is already risky, a voice note is transcribed by Muse Voice Transcribe, the transcript is masked and assessed like any message, and the audio is processed in memory and never stored. Proven end to end on real audio. Unlike text, the audio does reach Meta's transcription service; the consent text and the "what it does not claim" section say so.
- **The app as a child and parent see it.** The dcAI logo and colours, flat illustrations drawn in code (light and dark), onboarding in four steps (connect with the parent's code, read the consent together with two confirmations and the full text, create the parent PIN, switch protections on), then Home, Protection and Settings tabs. Each protection shows an indicator, and its page says what it does, what stays on the phone and what is sent. Switching a protection off needs the parent PIN and is reported to the parent. Indonesian and English, following the phone's language by default and selectable per app.
- **Images, judged on the phone.** An app with the dcAI SDK asks dcAI about an image before it shows or sends it, by binding to a signature-protected service and granting read access to that one image. ML Kit's bundled models find faces and text on the phone; the text goes through the same masking rules as messages. Faces and personal data (school, name, address, phone) in an image the child is about to share are blurred before it is sent. A received image is looked at only when its conversation is already at `perhatian` or above, and its text is masked and assessed like a message. The image never leaves the phone; the server gets a label (category, action, score, model). If dcAI blurs by mistake, the child shows the parent, who enters a PIN set at pairing and decides on the child's phone. A confirmed false detection is remembered on the phone by perceptual hash and raises that category's threshold in small capped steps (tier 1), and reaches the server as a label and a rounded score without the image (tier 2).
- **Sites, matched on the phone.** A DNS-only VPN: the phone's DNS server is an address inside the VPN and only that address is routed into it, so app traffic never passes through dcAI. Each looked-up name and its parent domains are matched on the phone against category lists built from UT1 Blacklists (CC BY-SA 4.0): adult, gambling, scams, malware, dating, drugs and hate, about 5.1 million domains in 26 MB of 40-bit hashes, so the phone holds no readable list. A listed site gets "no such domain" and the child a notification saying which category and why; any other name goes to the network's own resolver. The server receives the category, at most once per category in 30 minutes, never the site's name or a lookup history. The child can show a held site to the parent, who allows it on the phone with the PIN; the server gets a false-detection note with the category only. The VPN key icon shows the whole time, and switching the VPN off is an event for the parent.
- **Backend for the child's phone.** A parent creates a single-use pairing code; the phone trades it for a device token stored only as a hash. The phone reads its configuration (scopes it may use, age range, language), reports which protection services are on (a service switched off is an event for the parent), sends flagged messages, image labels (never pixels) and false detections the parent confirmed (stored without child or device id).
- **One queue per conversation.** The phone gets `202` in milliseconds; analysis runs in the background. Messages that arrive together share one stage 2 call and one Guide call, for the final level.
- **Parent dashboard and homepage** (Next.js 16): level for the last 7 days, the latest insight with conversation starters, what the child was told and verified help channels, events, conversations (pattern and explanation, no text), the phone's protection state, adding a child with consent and a pairing code, consent per scope, unpairing a phone, deleting a child's data. Indonesian and English. Updates live.
- **Facts page** (`/fakta`): published figures for each risk dcAI addresses (UNICEF, WHO/Europe, The Lancet, Disrupting Harm Indonesia, PPATK, BNPT and others), each quoted as its source states it and linked to the page that was checked. These are the only figures in the product not measured by this project.
- **Ask dcAI.** A parent asks in their own words; Muse Spark answers through function tools that are the dashboard's own queries, so it can see nothing the dashboard does not show. Children are aliases ("Anak A") in everything the model receives, names inside any text included. The answer is checked in code (no links, phone-like numbers or surveillance wording) and replaced by a fixed summary if it fails. Questions and answers are not stored.
- **Time online.** The parent sets daily limits for school days and weekends, limits per category (video, games, social, other), bedtime with a wind-down reminder, breaks after long short-video sessions, and apps that are always allowed. The phone counts foreground time from Android's usage access (app names and minutes, never what is inside an app), reminds the child before time runs out, and shows a break screen at a limit or at bedtime. The child can ask for more time with a short reason, masked on the phone and again on the server; Muse Spark suggests allow, allow part or not now, and the parent decides on the dashboard, which reaches the phone over the live stream. The server keeps minutes per category per day, bedtime minutes and the longest session. Muse Spark also writes a weekly summary for the parent from aggregate numbers and can propose limits, which change nothing until the parent saves them.
- **Live updates over SSE** with `Last-Event-ID` replay: the phone receives levels with a reviewed template nudge at once, then the model's nudge; the dashboard receives events, assessments and insight. Parent insight never goes to the phone.
- **58 synthetic scenarios** (621 messages, seven groups, including invitations to fights, drugs, alcohol or weapons for ages 10 to 17), with a locked 40/18 dev/test split. New scenarios join the split by the same hash, so no earlier id moved.

### Not built yet

In build order: a sensitive-image classifier (sexual content, violence) in the slot that exists on the phone, a small on-phone text classifier (ExecuTorch) distilled from the same teacher, per-category site settings for the parent, voice recording in the Android app (the backend route and transcription are done).

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
uv run python -m app.risk.stage1_eval <endpoint>       # stage 1 on the dev split
uv run python -m app.scenarios.validate                # check the scenario files
uv run python -m app.scenarios.split --check           # check the locked split
```

Messenger Z, the sample chat app, can be driven from a computer for a recorded demo. The contact answers each thing the child sends; Enter sends what was typed:

```bash
adb shell am start -n dev.eziedutech.dcai.samplechat/.MainActivity --es demo open    # also focus, card, landscape, next, image, restart, back
adb shell input text "halo%skak" && adb shell input keyevent KEYCODE_ENTER
```

## Architecture

```
code/backpy/   FastAPI: llm (provider pool), privacy (masking), risk (stage 1, floor, stage 2,
               pipeline), guide, analysis (per-conversation queue), live (SSE broker), consent,
               auth, api (/v1, /v1/device), migrations (Alembic), tests
data/          scenarios (synthetic JSON, split.json), privacy (masking test cases)
eval/          measurement output (ids and labels only, no text)
code/frontnext/ Next.js: homepage, privacy, how the AI helps, parent dashboard, Ask dcAI.
               Its server holds the session in httpOnly cookies and forwards an allowlist of
               /v1 paths to the backend; the phone's API is not reachable from the browser.
code/distill/  OpenPipe ART: fine-tunes the stage 1 student on a serverless training service
               (code/distill/train.py).
code/android/  Kotlin: dcAI (pairing, foreground service, nudges, on-phone masking,
               dcAI keyboard, image checks, DNS-only site VPN) and a sample chat app, built with Gradle. Masking parity is
               tested against data/privacy.
docs/          architecture decision records
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

The site lists for the phone are built from UT1 Blacklists (about a minute, 150 MB download, 26 MB output in `data/blocklist/`, not committed):

```bash
uv run python -m app.blocklist.build
```

The dashboard (Node.js 25):

```bash
cd code/frontnext
npm ci
npm run dev -- --port 3100      # http://localhost:3100, expects the backend on :8000
```

### Deploying

`code/docker-compose.prod.yml` runs PostgreSQL, the API and the web app; on Dokploy it is a Compose service from this repository with the model variables, `DB_PASSWORD` and `SECRET_KEY` in its environment, and two domains on one host: `/` to `web:3000` and `/v1` to `api:8000`. The API migrates on start and builds the site lists from UT1 into a volume the first time (about five minutes). Release builds of the Android app point at the public host; debug builds at the emulator's host machine.

The site's download button offers the APK from the repository's GitHub release. For a new version: raise `versionCode` and `versionName` in `code/android/app/build.gradle.kts`, build `assembleRelease` with the signing variables set (`DCAI_KEYSTORE`, `DCAI_KEYSTORE_PASSWORD`, `DCAI_KEY_ALIAS`, `DCAI_KEY_PASSWORD`; the keystore stays outside the repository), publish a release `v<version>` with the file `dcai-guardian-<version>.apk`, then set `APK_VERSION` in `code/frontnext/lib/download.ts`. Without the signing variables, as in CI, the release build is unsigned.

## Configuration

| Variable | Purpose |
|---|---|
| `REASONING_ENDPOINTS`, `SCREENING_ENDPOINTS` | endpoint names in each pool; calls rotate across them |
| `META_API_KEY`, `META_API_BASE`, `MUSE_MODEL`, `META_REASONING_EFFORT` | Meta Model API endpoint `meta` (model ID from `GET /v1/models`) |
| `FIREWORKS_BASE`, `FIREWORKS_API_KEY`, `FW_MUSE_*` | Muse Spark on Fireworks |
| `<NAME>_BASE`, `<NAME>_API_KEY`, `<NAME>_MODEL`, `<NAME>_PROVIDER` | any other OpenAI-compatible endpoint, such as the Llama models and the distilled student |
| `<NAME>_PRICE_IN_PER_MTOK`, `_CACHED_`, `_OUT_` | prices for cost logs; without them the cost is logged as `unknown` |
| `<NAME>_JSON_MODE`, `<NAME>_REASONING_EFFORT` | per endpoint: `json_schema`, `json_object` or `none`; reasoning effort |
| `DATABASE_URL` | SQLite or PostgreSQL |
| `SECRET_KEY` | signs 15-minute access tokens; refresh tokens rotate |
| `PAIRING_CODE_MINUTES`, `DEVICE_MESSAGES_PER_MINUTE` | pairing code lifetime; per-phone message limit |
| `SSE_HEARTBEAT_SECONDS`, `SSE_MAX_SECONDS` | stream heartbeat; streams close after this and clients reconnect |
| `SITE_LISTS_DIR`, `SITE_EVENT_MINUTES` | where the built site lists are (default `data/blocklist`); one parent event per site category in this window |

`.env.example` lists every variable.

## Results

### Tests

| Suite | Result |
|---|---|
| Unit and API tests on SQLite | 360 passed |
| The database tests again on PostgreSQL 18 (CI) | 102 passed |
| Dashboard: type check, lint, production build | passing |
| Android: unit tests (masking parity, image rules, PIN, site list parity, DNS packets, time rules), lint, debug APK | 35 passed |

### Full pipeline on the locked test split (final)

16 held-out scenarios, 177 messages, played message by message through stage 1 (Llama 3.3 70B), the rule floor and stage 2 (Muse Spark). The prompt was never tuned on these, so this is the honest measure. Expected levels are dataset drafts.

| Measure | Result | Spec target |
|---|---|---|
| Risky approaches reaching `waspada` or higher | 4 of 4 | at least 0.9 |
| Ordinary and hard cases reaching `waspada` or higher | 1 of 7 | at most 0.1 |
| Truly ordinary chats staying `aman` | 5 of 5 | |
| Detection delay, median | 2 messages (n=11) | at most 2 |
| Final level exactly as expected | 12 of 16 | |
| Self-harm flagged for a support response | 1 of 1 | |
| Score never decreased | 16 of 16 | |
| Messages without a complete analysis | 0 of 177 | |
| Cost of the whole run | USD 0.32 (0 calls unpriced) | |

- **One hard case over-escalates.** A benign look-alike (`kasus_sulit-008`) reaches `waspada`, the single false alarm; all five ordinary chats stayed `aman`. This is the `0.14` above the `0.1` target.
- **Detection delay sits at the target,** median 2 messages: the staged approaches are caught, a couple of messages after the dataset marks the start.

Full tables are in `eval/pipeline/test.md`. Run it with `make eval-test`.

### Full pipeline on the dev split

34 synthetic scenarios played message by message, used to tune the prompt. Expected levels are dataset drafts.

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

### dcAI on an emulator, one live run

On an Android 16 (API 36) emulator, with the backend and real models: a parent paired the
phone with a code; the persistent "dcAI aktif" notification appeared; the sample chat app
played a staged-approach scenario; each message was masked on the phone and sent; the
backend reached level `waspada` with patterns `meminta_data_pribadi` and `pindah_kanal`;
and the nudge arrived on the child's phone as a notification. Running it surfaced four
Android-specific fixes (regex engine, input-method check, cleartext config, notification
permission), now in the code.

### Sites on the emulator, one live run

Same emulator, real lists built from UT1 (5.1 million domains):

| Step | Result |
|---|---|
| The phone downloads the seven lists and checks each SHA-256 | 26 MB on the phone |
| `example.com`, `www.google.com` | resolved as usual through the network's resolver |
| `0-xbets.net`, from UT1's gambling list | "unknown host"; the child got "dcAI menahan situs berkategori judi"; the parent event `situs_judi` |
| The parent allowed it with the PIN | resolved again; feedback stored as `domain`, `judi` |
| The site's name in the database or the server log | absent |

Running it found one defect, fixed: the adult list (23 MB), sent in one write, was cut off on the emulator's network; the list is now streamed in chunks and the phone retries once.

### Images on the emulator, one live run

Same emulator, sample chat app, synthetic pictures drawn on the phone (every name, number
and address invented):

| Image | What dcAI did |
|---|---|
| A student card the child is about to share | School, name, address and phone blurred; label `teks_pribadi` sent; parent event `gambar_data_pribadi` |
| A landscape | Left as it is; nothing sent |
| The same card, after the parent marked it a false detection with the PIN | Left as it is (perceptual hash match); feedback stored as a label and score |
| A screenshot from the stranger saying "move to another app", in a chat already at `mendesak` | Text recognised and sent masked as a message for the assessment |

Running it found two defects, both fixed: the decoder treated every image as unreadable,
and OCR read "Jl." as "JI.", which hid the address from the masking rules. In the last
image, OCR did not yield the account handle as personal data, so that image was not
blurred; its text still went through masking.

### Phone path, one live run

Four synthetic messages from a stranger in a game chat, sent at once through `/v1/device/messages`, live models, one run (not a benchmark):

| Moment | Time after the first message |
|---|---|
| Each message accepted (`202`) | 10 to 21 ms |
| Level `perhatian` with a template nudge on the phone stream | 2.0 s |
| Level `mendesak` with a template nudge | 5.9 s |
| The model's nudge for `mendesak` | 15.6 s |

Model calls: 4 stage 1, 1 stage 2, 1 Guide. Before the queue merged them, the same run made 2 Guide calls and reached `mendesak` later, because a Guide for the out-of-date `perhatian` level held the queue.

### Ask dcAI, one live question

"Apa yang terjadi minggu ini?" on the synthetic run above: 3 Muse Spark turns (two tool calls, then the answer), about 10 s, about USD 0.012. The answer used only dashboard data, named the child after the alias was put back, and said that message text is not stored.

### Invitations to delinquency, a new label

`ajakan_berbahaya` covers invitations to fights (tawuran), offering drugs, pills or alcohol, and carrying sharp weapons, from either side of the chat. One label sets the floor at `waspada`. Six new `kenakalan` scenarios and two look-alike hard cases (silat sparring, an anti-drug poster project), run through the full pipeline with student v2, trained before the label existed (`eval/pipeline/dev-kenakalan.md`, `test-kenakalan.md`), and with student v3, retrained with it (`dev-student-v3.md`, `test-student-v3.md`):

| Scenario | Split | Expected | v2 (default) | v3 |
| --- | --- | --- | --- | --- |
| kenakalan-001 | dev | waspada | waspada | mendesak |
| kenakalan-002 | dev | waspada | waspada | mendesak |
| kenakalan-003 | dev | mendesak | mendesak | mendesak |
| kenakalan-004 | dev | waspada | mendesak | mendesak |
| kasus_sulit-010 (silat) | dev | aman | aman | aman |
| kasus_sulit-011 (poster) | dev | aman | waspada | aman |
| kenakalan-005 | test | waspada | waspada | mendesak |
| kenakalan-006 | test | waspada | mendesak | mendesak |

With both students all six reach `waspada` or higher. With v2 the poster project was a false alarm; v3 keeps both look-alike cases at `aman`, and ends all five scenarios expected at `waspada` one level higher, at `mendesak`. Stage 1 for this label:

| Student | Dev (11 messages) | Test (3 messages) |
| --- | --- | --- |
| v2 | precision 0.67, recall 0.55 | precision 0.75, recall 1.00 |
| v3 | precision 1.00, recall 0.55 | precision 1.00, recall 0.33 |

v3 no longer puts the label on harmless messages, and still misses about half of the invitations; the rest of each conversation brings it to `waspada`.

### Citizenship Guide

9 cases covering every situation (approach, child bullied, child bullying, shared data, distress, general) at `perhatian`, `waspada` and `mendesak`, in Indonesian and English. All 9 were answered by the model and passed the schema and tone rules. Latency was 4 to 8 s on the Meta Model API and 18 to 27 s on Fireworks. The tone review by a person (spec rubric, target 4 of 5) is pending.

Found and fixed on the way: Fireworks timed out at 20 s on every guide call (the guide now gets 45 s); English output mixed in Indonesian words (now rejected and replaced by a template); and Indonesian reduplication lost its hyphen ("hati hati", now repaired in code).

### Distillation: Muse Spark teacher, Llama 3.1 8B student

The teacher labelled the 366 dev messages (USD 0.58); the student is LoRA SFT on a serverless training service, trained on the exact production stage 1 input. Measured on the locked test split.

| Stage 1 on the test split | Recall | Precision | Ordinary messages labelled | Self-harm caught | Cost |
|---|---|---|---|---|---|
| Llama 3.3 70B (previous default) | 0.84 | 0.72 | 0 of 41 | 3 of 3 | USD 0.106 |
| Llama 3.1 8B, base | 0.89 | 0.52 | 5 of 41 | 2 of 3 | USD 0.033 |
| Student v1 | 0.73 | 0.84 | 0 of 41 | 0 of 3 | USD 0.033 |
| **Student v2** | **0.81** | **0.91** | **0 of 41** | **2 of 3** | **USD 0.033** |

| Full pipeline on the test split | 70B screening | Student v2 |
|---|---|---|
| Risky approaches reaching `waspada` or higher | 4 of 4 | 4 of 4 |
| Ordinary and hard cases reaching `waspada` or higher | 1 of 7 | 1 of 7 |
| Detection delay, median | 2 messages | 0 messages |
| Self-harm flagged for support | 1 of 1 | 1 of 1 |
| Cost of the run | USD 0.32 | USD 0.17 |

- **v1 never labelled self-harm.** Trained on the data as is, where 79% of messages carry no label and self-harm appears 6 times, it learned that "no label" is almost always right. v2 rebalances the classes from the training data's own counts.
- **The test split was used twice for the student** (v1 found the regression, v2 is the fix), so v2's test numbers are not from an untouched split.
- **Student v3 was evaluated and not adopted.** Retrained the same way on the 40-scenario dev split, which now holds the invitation scenarios (teacher USD 0.69, 670 training examples after balancing). On the 18-scenario test split its pipeline matches v2: risky approaches 4 of 4 at `waspada` or higher, ordinary and hard cases 1 of 7, self-harm flagged 1 of 1, score never decreased 18 of 18, USD 0.23 against 0.22. Final levels exactly as expected drop from 14 to 11 of 18, and on dev one risky approach ends at `perhatian` (7 of 8). The test split was used a third time, for this decision. Missing a risky approach weighs more than a false alarm, so v2 stays the default.

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
- **It gives no medical or psychological advice and makes no diagnosis.** When a child's messages show distress, the child is encouraged to talk to a trusted adult today, the parent is asked to be with the child, and both see help channels from a manually verified list. Nothing in dcAI assesses or treats a child's health.
- **Masking does not catch everything.** It misses names the system does not know and that are not introduced with a phrase such as "namaku", a class without a school, and places described in words ("near the blue shop").
- **Free Meta credits allow Meta to use request content for product improvement.** Only synthetic data is sent. Real use needs the `meta` endpoint removed or paid usage.
- **Not everything is processed on the device.** Masked messages go to model providers, and a voice note's audio reaches Meta's transcription service before its transcript is masked.
- **No sensitive-image model ships, and none has been tested by us.** The phone has the slot, the thresholds and the review flow, tested with a stand-in score. We do not create or collect sexual images of anyone to test a classifier. A licensed classifier's accuracy will be the figure its source states, not ours, and the app says on the child's screen that sensitive-image detection is off until one is installed.
- **Site protection works at the DNS level, and can be gone around.** A browser with its own encrypted DNS, an app with a built-in resolver, or another VPN skips it; switching the VPN off is reported to the parent. A false match is possible about once in 200,000 checks. UT1's coverage of sites aimed at Indonesia, gambling in particular, has not been measured. When the network gives no resolver, lookups go to a public one (1.1.1.1).
- **The invitation label is new, and the screener was trained before it existed.** Student v2 finds 6 of 11 invitations on dev with precision 0.67, so it raises false alarms (one of two look-alike hard cases on dev) and can miss a single invitation in an otherwise ordinary chat. A retrained v3 removed the false alarm but missed more risk and was not adopted. See Results.
- The consent text has not had legal review.

## Credits and licenses

- **Meta Muse Spark** through the Meta Model API and Fireworks; **Meta Llama 3.3 70B and 3.1 8B** through an open-weights inference provider (Llama 3.x Community License).
- **UT1 Blacklists**, Universite Toulouse Capitole, CC BY-SA 4.0: the site lists on the phone are hashed adaptations under the same license.
- **Google ML Kit** face detection and text recognition, bundled on-device models (ML Kit terms).
- **FastAPI**, **uvicorn**, **pydantic**, **httpx**, **SQLAlchemy**, **Alembic**, **psycopg**, **argon2-cffi**, **PyJWT**, **pytest**, **respx**, **ruff**, **PostgreSQL**: their respective open source licenses.

## How this was built

A Code Assistant was used to accelerate development and debugging. Design decisions, measurements and claims were checked against real runs.

## About digitalsafe.app

dcAI is one of the main pillars of digitalsafe.app, a startup building an ecosystem for digital education, ethics and safety, with an AI platform for each group of users:

- **dcAI** (this repository): digital safety and ethics for school-age children and their families.
- **C.I.T.R.A.** (Core Integrity & Trustworthy Research Assistant): an AI research assistant that puts academic integrity first, for students, researchers and academics.
- **Belajar Z**: an agentic AI LMS that helps teachers run learning in a way that is ethical, accountable and transparent.
- **Numeria Arena**: safe, friendly mathematics games and learning through Extended Reality (XR/VR) and AI.

## License

MIT, see [LICENSE](LICENSE).
