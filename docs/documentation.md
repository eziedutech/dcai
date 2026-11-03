# dcAI documentation

Reference for dcAI as released on 3 November 2026: web at <https://dcai.digitalsafe.app>, Android
v0.3.10. Figures and limits are in the README ([Results](../README.md#results),
[What it does not claim](../README.md#what-it-does-not-claim)). All data is synthetic.

## 1. Roles

| Role | Where | Can do |
|---|---|---|
| Child (10 to 17) | dcAI on the phone | See which protections are on and what each sends; get reminders; ask for more time; show a held site or image to the parent |
| Parent (guardian) | `/dasbor`, PIN on the child's phone | Add a child, give consent per scope, pair a phone, set time rules, read insight, ask dcAI, decide time requests and false detections, delete data |
| School staff | `/sekolah` | Create classes, share join codes, see anonymous counts per class |

A guardian reaches only their own children (others answer 404). A school never reaches a child.

## 2. Setup

1. Parent registers at `/daftar`, adds a child (name, age range, language) and grants consent per scope.
2. Dashboard shows a single-use pairing code.
3. On the child's phone, install `dcai-guardian-0.3.10.apk` and follow the four onboarding steps:
   enter the code, read the consent together (two confirmations and the full text), create the
   parent PIN, switch protections on.
4. The phone shows the persistent "dcAI aktif" notification for as long as dcAI runs.

## 3. Consent scopes

| Scope | Covers |
|---|---|
| `percakapan` | Chat messages from notifications and apps with the dcAI SDK; flagged messages sent masked |
| `layar` | Screen text read in any app through the accessibility service; masked |
| `keyboard` | Text typed on the dcAI keyboard; masked |
| `gambar` | Images judged on the phone; only labels leave it |
| `domain` | Sites matched on the phone; only the category of a held site leaves it |
| `waktu` | Minutes per app category per day; limits, bedtime, focus mode |
| `sekolah` | Child counted in a class aggregate |

- Analysis runs only while the scope's consent is active. Records are append-only.
- The text is versioned (current `2026-11-02.1`). A material change pauses the affected scope
  until the parent reads and agrees again; a minor change shows a "text changed" card. Older
  texts stay readable; Settings show the version per scope.

## 4. Message analysis (Grooming Shield)

Pipeline: mask, stage 1, rule floor, stage 2, Guide.

- **Masking** by fixed rules on the phone and again on the server: names, phone numbers, emails,
  card numbers, addresses, schools. Python and Kotlin share 55 test cases.
- **Stage 1**, per message: Llama 3.1 8B student distilled from Muse Spark; Llama 3.3 70B backup.
  Labels: building closeness fast, asking for secrecy, moving to another app, asking for personal
  data or photos, gifts, testing limits, pressure, bullying, dangerous invitations (fights, drugs,
  alcohol, sharp weapons), distress.
- **Rule floor**: deterministic minimum per pattern. Score = max(model, rules, previous score).
  It never drops within a conversation. A model failure shows `perhatian` with "analysis
  unavailable", never `aman`.
- **Stage 2**, Muse Spark: assesses the masked conversation window only when it shows a signal.
- **Levels**: `aman` 0 to 29, `perhatian` 30 to 59, `waspada` 60 to 84, `mendesak` 85 to 100
  (Safe, Needs attention, Alert, Urgent). Each carries a confidence and is marked as an estimate.
- **Queue** per conversation: the phone gets `202` at once; messages arriving together share one
  stage 2 call and one Guide call.
- **On-phone mode** (optional, Settings): Llama 3.2 1B student on ExecuTorch in process
  `:ondevice`; ordinary messages judged and discarded on the phone, risky ones sent. Offered on
  phones with at least 5 GB RAM that are not low-RAM devices; download about 0.8 GB with the
  device token, SHA-256 checked; online is the fallback. "Dibuat dengan Llama" shows in the app.

### Message sources on the phone

| Source | Needs |
|---|---|
| Screen text, any app, any keyboard (main source) | `layar`, dcAI enabled in accessibility settings |
| Chat notifications (other person's side) | notification access |
| dcAI keyboard (child's own typing) | `keyboard`, dcAI chosen as keyboard |
| Apps with the dcAI SDK (Messenger Z) | signature-permission broadcast |

All four use one masking path; only flagged, masked messages are sent.

## 5. Citizenship Guide

Muse Spark writes, per level change or first distress:

- **Child**: a reminder of at most two sentences with the reason, no blame.
- **Parent**: what was seen, why it matters, three conversation starters, what to do and avoid,
  a one-minute lesson.
- **Fallback**: reviewed templates for every situation, level and language.
- **Checks in code**: rejects blame toward the child, punishment advice, links, phone-like
  numbers, mixed languages.
- **Help channels** only from `data/guide/channels.json`; only manually verified entries carry a
  number.
- **Distress**: the child is encouraged to talk to a trusted adult today; the parent is asked to
  be with the child.

The phone receives the level with a template reminder at once, then the model's reminder, over
SSE with `Last-Event-ID` replay. Parent insight never reaches the phone.

## 6. Images and video

- Apps with the dcAI SDK ask dcAI before showing or sending an image (signature-protected
  service, read access to that image only).
- ML Kit on the phone finds faces and text. Text is masked like a message.
- **Sharing**: faces and personal data (school, address, phone, account handles, recognised names)
  are blurred before sending. A name after a label such as "Nama:" is not recognised.
- **Receiving**: an image is checked only when its conversation is at `perhatian` or above; its
  text is assessed like a message.
- **Sexual content**: Falconsai `nsfw_image_detection` (LiteRT int8). SDK apps blur the picture
  fully before it shows. Other apps: the screen reader cuts out each picture in the chat and
  scores it; the child is reminded, the parent gets a label once per picture.
- **False detection**: the child shows the parent; the parent decides with the PIN. Remembered on
  the phone by perceptual hash with a capped threshold step; the server gets a label and a rounded
  score.
- **Video** (test builds with `-Pdcai.video=true` only): up to four frames judged on the phone;
  video covers in other apps reported as video.
- Images and video never leave the phone; the server stores category, action, score, model.

## 7. Sites

- DNS-only VPN: only the DNS address is routed into it; app traffic does not pass through dcAI.
- Hashed category lists from UT1 Blacklists: adult, gambling, scams, malware, dating, drugs, hate.
  No readable list on the phone.
- A listed site gets "no such domain"; the child gets a notification with category and reason.
- The server gets the category, at most once per category per 30 minutes; never the site name or
  a history.
- The parent can allow a site with the PIN; the server gets a false-detection note with the
  category. Switching the VPN off is an event for the parent.

## 8. Time online and focus mode

- Daily limits for school days and weekends; limits per category (video, games, social, other);
  bedtime with a wind-down reminder; a break after long short-video sessions; always-allowed apps.
- **Focus mode**: only the apps the parent picks stay open.
- The phone counts foreground minutes from usage access (app names and minutes). It reminds before
  time runs out and shows a break screen at a limit or bedtime.
- **Time requests**: the child asks with a short reason (masked); Muse Spark suggests allow, allow
  part or not now; the parent decides; the answer reaches the phone live.
- **Weekly summary** by Muse Spark from aggregate numbers; proposed limits apply only when the
  parent saves them.

## 9. Parent dashboard (`/dasbor`)

- One tab set per child: Summary, Time online, School, Phone, Settings.
- Summary: level for 7 days, latest insight and conversation starters, what the child was told,
  verified help channels, events, conversations (pattern and explanation, no text).
- Phone: protection state per service; unpair.
- Settings: consent per scope and text version, rename the child, clear history, delete all of the
  child's data (phone told, token ended).
- Account: change password, sign out of every device.
- **Ask dcAI** (`/dasbor/tanya`): questions in the parent's own words; Muse Spark answers through
  the dashboard's own queries as function tools; children become aliases ("Anak A"); answers are
  checked for links, numbers and surveillance wording; nothing is stored.
- Live updates; Indonesian and English.
- Public pages: `/`, `/privasi`, `/cara-kerja`, `/fakta`, `/next`, `/ketentuan`, `/panduan`.

## 10. School module (`/sekolah`)

1. School signs up (`/sekolah/daftar`); staff accounts are separate from parent accounts.
2. Class created; 6-character join code shown once, stored as a hash.
3. Parent grants `sekolah` for the child and enters the code; can leave at any time, effective at
   once.
4. School sees counts per level per class for the last 7 days: shown from 5 children, "needs
   support" from 10.
5. Other schools get 404; the audit log holds ids only.

## 11. Messenger Z

Sample chat app with the dcAI SDK (`dcai-messenger-z-0.3.10.apk`), in English on an English phone.
Synthetic contacts: Bima (stranger), Science Group 8B, Mom, Dinda (Kak Bima, Kelompok IPA 8B, Mama
in Indonesian). Contacts answer each message. Pictures and video come
from the photo picker. Demo mode from a computer:

```bash
adb shell am start -n dev.eziedutech.dcai.samplechat/.MainActivity --es demo open
```

Other values: `focus`, `card`, `landscape`, `next`, `image`, `restart`, `back`.

## 12. What leaves the phone

| Data | Leaves the phone | Stored on the server |
|---|---|---|
| Ordinary message | online mode: masked, for analysis; on-phone mode: no | no text, ever |
| Flagged message | masked | labels, level, explanation; no text |
| Image, video | no | label (category, action, score, model) |
| Site | no | category of a held site |
| App use | app category minutes | minutes per category per day, bedtime minutes, longest session |
| Time request reason | masked | masked reason |

Conversation windows live in memory only. Tests fail when message text reaches a log or a
database column.

## 13. Models

| Task | Model |
|---|---|
| Stage 1 screening | Llama 3.1 8B student (distilled from Muse Spark); Llama 3.3 70B backup |
| Stage 2, Guide, Ask dcAI, time advice, weekly summary | Muse Spark (Meta Model API; Muse Spark Open on Fireworks and Baseten) |
| On-phone screening (optional) | Llama 3.2 1B student, ExecuTorch |
| Images | ML Kit faces and text; Falconsai NSFW classifier, LiteRT |

`LLMClient` rotates calls across a pool of providers, fails over on rate limits and outages, and
validates every output against a schema. Model IDs and prices come from the environment. Built
with Llama. Training rounds and research: README [Research and training](../README.md#research-and-training).
Planned: one small multimodal model on the phone in place of the separate text, image and video
models.

## 14. API (`/v1`)

| Group | Prefix | Auth |
|---|---|---|
| Health | `/v1/health` | none |
| Guardian auth | `/v1/auth` (register, login, refresh, logout, logout-all, change-password, me) | guardian token |
| Children, consent, insight, events, Ask dcAI | `/v1/children`, `/v1/consents`, `/v1/ask` | guardian token |
| Phone | `/v1/device` (pair, config, heartbeat, messages, images, detection feedback, sites, usage, time requests, on-phone model download, live stream) | device token |
| School | `/v1/school` (register, login, me, classes, overview) | staff token |

The browser talks only to the Next.js server, which keeps sessions in httpOnly cookies and
forwards an allowlist of paths. The phone API is not reachable from the browser. Routes are in
`code/backpy/app/api/`.

## 15. Operation

- **Production**: Dokploy, three services: `dcai-db` (PostgreSQL 18), `dcai-api`, `dcai-web`.
  Each push to `main` deploys API and web. Steps in [deploy.md](deploy.md).
- **Local**: see README [Running locally](../README.md#running-locally).
- **Tests**: `cd code/backpy && uv run pytest`; PostgreSQL variants with `DCAI_TEST_PG_URL`;
  Android `./gradlew :app:testDebugUnitTest`.
- **APK release**: raise `versionCode`/`versionName` in `code/android/app/build.gradle.kts`, copy
  the image model into `app/src/main/assets/vision/`, build `assembleRelease` with the signing
  variables, publish release `v<version>`, set `APK_VERSION` in `code/frontnext/lib/download.ts`.
