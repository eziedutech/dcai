# ADR 0002: Device ingest, per-conversation queue and live updates

Status: accepted, 27 Oct 2026

## Context

dcAI Guardian runs on the child's phone. The phone sends only
flagged, masked messages, image labels and confirmed false detections. Stage 2 measured
p50 6.1 s and p95 15.3 s on the dev split, and the Guide adds 4 to 10 s, so a phone that
waits for the full analysis would hold a connection for up to 25 s per message, and a
child about to answer "send me your photo" would get no guidance in that time.

## Decision

- **Pairing.** The guardian creates a single-use code (8 characters without look-alike
  characters, minutes to live, stored as a hash). The phone trades it for an opaque device
  token (`dcd_` prefix, stored as a hash). Revoking the device or erasing the child ends the
  token. Pairing needs an active consent.
- **One queue per conversation, in process.** `POST /v1/device/messages` answers `202` at
  once. A worker per conversation handles messages in order. When several are waiting,
  stage 2 and the Guide run only for the last of them, with the debt carried forward, so
  an out-of-date level is never guided. Consent is checked again when a message leaves the
  queue. The simulator endpoint `/v1/messages/analyze` goes through the same queue and waits.
- **Level first, Guide after.** The level is stored and published as soon as stage 2
  returns, with the reviewed template nudge for the situation; the model's nudge follows.
- **SSE with replay.** One in-memory broker with keys `device:<id>` and `child:<id>`, the
  last 100 events per key, `Last-Event-ID` replay, a heartbeat and a maximum stream length
  so clients reconnect and re-authenticate.
- **What the phone may see** is its configuration, the levels of its own conversations and
  nudges. Parent insight and the rationale never go to the phone.
- **Image labels** carry trigger, category, action, score and model version. They become
  events for the parent; they do not yet feed the risk score (stage 5).
- **False detections** confirmed by the parent are stored without child, device or
  conversation id, with the score rounded to 5.

## Consequences

- One API process only. Several workers or hosts need a shared bus (PostgreSQL
  LISTEN/NOTIFY) and a persistent queue. A restart drops messages still waiting in a queue;
  the phone does not resend them yet.
- The phone must treat a `nudge` event as replacing the template nudge of the same
  conversation, so the child sees one card that improves, not two.
- The rate limit per phone (30 messages a minute by default) is in memory and per process.
