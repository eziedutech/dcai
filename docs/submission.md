# dcAI submission summary

The single source for the README header, the hackathon submission form and the pitch. Every
figure here is copied from the README's Results section, which takes them from `eval/`. Status
as of 31 October 2026.

## Name and one-liners

- **Name:** dcAI, Digital Citizenship AI, Family Safety Guardian. One pillar of digitalsafe.app
  by EZI EDUTECH.
- **Short (one line):** An AI companion on the child's phone that guides children at the moment a
  chat turns risky, gives parents insight and conversation starters, and gives schools an
  anonymous class-level picture.
- **Elevator pitch:** dcAI guides the child first, then helps the parent understand. When a chat
  starts to follow a risky pattern (grooming, bullying, invitations to fights or drugs, sharing
  personal data, distress), the child gets a short, friendly reminder with the reason, and the
  parent learns what kind of pattern appeared and how to talk about it. Message text is never
  shared and never stored. With a parent's separate consent, a school sees only anonymous counts
  per class, never a single child.
- **Event:** Meta Global AI Developer Hackathon (Cerebral Valley, 26 Oct to 4 Nov 2026). MVP;
  all data is synthetic.

## Links

- Live: <https://dcai.digitalsafe.app> (homepage, parent dashboard at `/dasbor`, school
  dashboard at `/sekolah`, facts at `/fakta`, privacy at `/privasi`).
- Android app: the download button on the homepage (APK 0.3.4, Android 11+, API 30+).
- Phone API: `https://dcai.digitalsafe.app/v1` (health at `/v1/health`).
- Code: <https://github.com/eziedutech/dcai>, MIT license.

## Who it serves

| Who | What they get |
|---|---|
| Child (10 to 17) | A reminder of at most two sentences, at the moment it matters, that never blames; a site or image held with the reason; a break screen at a limit or at bedtime; a way to ask for more time or show a mistake to a parent. dcAI is always visible on the phone (persistent notification, no hidden mode). |
| Parent | Level for the last 7 days, insight with what was seen, why it matters, three conversation starters, what to do and avoid; events; time online and focus rules; Ask dcAI; consent per scope; one-call deletion of a child's data. |
| School | Anonymous counts per level for each class, shown only when enough children take part. No names, no insight, no conversation, no way to point at a child. |

## What is built

1. **Grooming Shield (risk pipeline).** Text is masked first (names, numbers, emails, card
   numbers, addresses, schools). Stage 1, a Llama 3.1 8B student distilled from Muse Spark,
   labels each message with behaviour patterns; a deterministic rule floor sits under it;
   stage 2, Muse Spark, assesses the conversation window when it shows a signal. The score is
   the highest of the model, the rules and the previous score, so it never drops within a
   conversation, and a model outage is never shown as safe.
2. **Citizenship Guide** (Muse Spark): the child nudge, the parent insight and a one-minute
   lesson, with reviewed templates for every situation, level and language when the model
   fails. Code rejects blame, punishment advice, links, phone-like numbers and mixed languages;
   help channels come only from a manually verified list.
3. **Ask dcAI** (Muse Spark with function tools that are the dashboard's own queries): a parent
   asks in their own words; children are aliases in everything the model sees; questions and
   answers are not stored.
4. **The Android app** (Kotlin, API 30+, v0.3.4). Pairing by a single-use code, onboarding with
   consent read together, a parent PIN to switch protections off (reported to the parent).
   Four message sources share one on-phone masking path: screen text through an accessibility
   service (the main source, any app, any keyboard), chat notifications for the other person's
   side, the dcAI keyboard, and apps with the dcAI SDK (sample: Messenger Z). Only flagged,
   masked messages leave the phone.
5. **Images, judged on the phone** (ML Kit face and text detection): faces and personal data
   in an image the child is about to share are blurred before it is sent; the image never
   leaves the phone, only a label does. A parent can confirm a false detection with the PIN.
6. **Sites, matched on the phone**: a DNS-only VPN checks names against hashed category lists
   from UT1 Blacklists (adult, gambling, scams, malware, dating, drugs, hate; about 5.1 million
   domains). The server gets only the category, never the site or a history.
7. **Time online**: daily limits for school days and weekends, limits per category, bedtime
   with a wind-down reminder, breaks after long short-video sessions (doomscrolling), always
   allowed apps, and **focus mode** (only allowed apps plus phone essentials open). The child
   can ask for more time; Muse Spark suggests, the parent decides; a weekly summary from
   aggregate numbers.
8. **Parent dashboard and homepage** (Next.js 16), Indonesian and English, live over SSE.
9. **School module** (aggregate only), described below.
10. **Consent and data rights**: analysis runs only under active consent, per scope; consent
    records are append-only (a database trigger refuses updates); one call deletes everything
    about a child and ends the paired phone's token.

## How the school module works

The school module lets a school see how its classes are doing as a group, without ever seeing a
child. It is opt-in per child, by the parent.

1. **A school signs up.** A teacher or principal registers at `/sekolah/daftar`, which creates
   the school and its first staff account (role `kepala`). Staff accounts are separate from
   parent accounts: a parent's or a phone's token cannot reach any staff endpoint, and a staff
   token cannot reach a child. The staff session is a 15-minute access token in an httpOnly
   cookie, and the web server forwards only three staff paths to the backend: the account, the
   class list and a class overview.
2. **The school creates a class** and receives a 6-character join code, shown once (the alphabet
   leaves out look-alike characters). Only a hash of the code is stored, so it cannot be listed
   again.
3. **The teacher shares the code with parents**, outside dcAI.
4. **The parent opts in.** In the dashboard, the parent grants the optional "School overview"
   scope for that child (consent version 2026-10-30.3 adds it, with its own paragraph), then
   enters the class code in Settings. Without the scope the join is refused; a wrong code is not
   found; joining twice changes nothing. The parent sees the classes the child is in and can
   leave any of them at any time.
5. **The school sees an aggregate.** For a class, the server takes the last 7 days and, for each
   member whose parent's school consent is active right now, reads two things: the child's
   highest current level across their conversations (`aman` when there is none) and whether a
   "needs support" event happened. It counts them per level and drops the per-child values.
   The response holds only the totals.
6. **k-anonymity.** Counts appear only when at least 5 consenting children are in the class;
   below that the class shows "not enough children yet". The more sensitive "needs support"
   count appears only from 10 children.
7. **Withdrawal is immediate.** If a parent withdraws the school scope, the child drops out of
   the counts on the next view, even before leaving the class. Deleting a child's data removes
   the membership too.
8. **Isolation and audit.** Staff of another school get "not found" for a class that is not
   theirs. The audit log records sign-up, class creation, joining and leaving by id only.

What a school never sees: a child's name or nickname, which child is at which level, insight,
conversations, events, images, sites or devices. The class list shows how many children joined.

### Parent and school, for one child

Two separate roles, two separate logins, no shared view. The school is always downstream of the
parent.

- **The parent is the guardian.** They install dcAI, give consent per scope, hold the PIN, and
  see the full dashboard (level, insight, events, time online, devices) at `/dasbor`. Without the
  parent there is no dcAI for that child.
- **The school has no link to the child.** A teacher signs in at `/sekolah` and sees only
  anonymous counts per level for a whole class. They cannot add, see or act on any one child.
- **The child reaches a class only through the parent**: the parent grants the school scope and
  enters the class join code. The school then counts that child as one number in the class total,
  under k-anonymity.
- **The parent can undo it at any time**: withdraw the scope or leave the class, and the child
  drops from the school's count at once. Deleting the child removes the membership too.
- **Nothing about one child flows between the two**: not from the school to the parent, not from
  the parent's dashboard to the school. The school's only output is a class-level aggregate.

Not built yet for schools: inviting more staff to the same school, a school-wide view across
classes, and per-case referral controlled by the parent.

## Meta AI in dcAI

| Role | Model | Where it runs |
|---|---|---|
| Stage 1 screening, per message | Llama 3.1 8B student (distilled), Llama 3.3 70B as backup | open-weights inference providers |
| Stage 2 assessment of the conversation window | Muse Spark | Meta Model API; Muse Spark Open on Fireworks and Baseten |
| Citizenship Guide (child nudge, parent insight, lesson) | Muse Spark | same pool |
| Ask dcAI, time-request advice, weekly summary, limit suggestions | Muse Spark | same pool |
| Training: teacher labels | Muse Spark | labelled the dev messages |
| Training: student | Llama 3.1 8B, LoRA SFT on the exact production prompt | OpenPipe ART on a serverless training service |

- One model interface (`LLMClient`) over a pool of OpenAI-compatible endpoints: calls rotate,
  fail over on rate limits and outages, and every output is validated against a schema.
- Model IDs and prices come from the environment, never from code.
- Under the models sit a deterministic rule floor and reviewed templates, so a model failure
  never lowers a level or leaves a child without guidance.
- Planned: a smaller distilled Llama running on the phone with ExecuTorch.

## Privacy and safety by design

- Masking on the phone before anything leaves; masked again on the server.
- No database column can hold conversation text (a test inspects the migrated schema); message
  text never reaches a log (tested with a sentinel string on every model path).
- Images never leave the phone; site names and browsing history never reach the server.
- The child always knows dcAI is on; no hidden mode; switching protection off needs the parent
  PIN and is reported.
- Parent insight never goes to the child's phone; a guardian reaches only their own children.
- The school sees counts only, under k-anonymity, and only with the parent's consent.

## Architecture and deployment

- Backend: FastAPI (Python 3.14), PostgreSQL 18, Alembic migrations, per-conversation queues,
  SSE live updates.
- Web: Next.js 16; the browser talks only to the web server, which holds sessions in httpOnly
  cookies and forwards an allowlist of paths.
- Android: Kotlin, foreground service, accessibility screen reader, notification listener,
  keyboard, image service, DNS-only VPN, time rules and break screen.
- Production: three services in one Dokploy project (managed PostgreSQL, API, web), so app
  rebuilds never touch the data. Each push to `main` deploys the API and the web.

## Results (synthetic data)

- **Full pipeline, locked test split** (16 scenarios, 177 messages): risky approaches at
  `waspada` or higher 4 of 4; ordinary and hard cases at `waspada` or higher 1 of 7; truly
  ordinary chats staying `aman` 5 of 5; median detection delay 2 messages; score never
  decreased 16 of 16; no message without a complete analysis (0 of 177).
- **Distillation**: student v2 stage 1 recall 0.81 and precision 0.91 against 0.84 and 0.72 for
  Llama 3.3 70B; the full pipeline with the student matches 70B on every safety measure, at USD
  0.17 against 0.32 for the run.
- **Citizenship Guide**: 9 of 9 cases answered by the model passed the schema and tone rules.
- **Phone path, one live run**: each message accepted in 10 to 21 ms; a template nudge on the
  phone at 2.0 s.
- **Tests**: 381 backend tests pass on SQLite (31 Oct 2026); the database tests also run on
  PostgreSQL in CI; Android unit tests, dashboard type check and lint pass.

## What it does not claim

- Not tested with real children or families; not yet reviewed by child-protection experts.
- Every assessment is an estimate and can be wrong; dcAI gives no medical or psychological
  advice.
- Masking does not catch everything; masked messages do go to model providers.
- No sensitive-image model ships yet.
- Site protection works at the DNS level and can be gone around.
- Free Meta credits allow Meta to use request content, so only synthetic data is sent.
- The consent text has not had legal review.

## What comes next

A sensitive-image classifier in the slot on the phone; a small on-phone text classifier
(ExecuTorch) distilled from the same teacher; per-category site settings for parents; more staff
per school and a school-wide view; expert review and a consented pilot.

## Ringkasan singkat (Bahasa Indonesia)

dcAI adalah pendamping AI di ponsel anak (10 sampai 17 tahun). Saat obrolan mulai mengikuti pola
berisiko, anak mendapat pengingat singkat yang ramah beserta alasannya, dan orang tua memahami
pola yang muncul serta cara membicarakannya. Isi pesan tidak pernah dibagikan atau disimpan.
Dengan persetujuan terpisah dari orang tua, sekolah hanya melihat jumlah anak per level di setiap
kelas, dan angka itu baru tampil bila minimal 5 anak ikut. Model Meta menjadi intinya: Muse Spark
menilai pola, menulis bimbingan, dan menjawab orang tua; murid Llama 3.1 8B hasil distilasi dari
Muse Spark menyaring tiap pesan.
