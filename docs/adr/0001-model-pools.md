# ADR 0001: Model access through pooled OpenAI-compatible endpoints

Status: accepted, 26 Oct 2026

## Context

The spec asks for one `LLMClient` interface with `MuseClient` and `OpenWeightsClient`, a
safe fallback when output is invalid, and cost logging. The owner wants load spread over
several providers so no single provider carries all calls. Muse Spark is reachable through
the Meta Model API and through Fireworks; small open-weights models are on several hosts.

## Decision

- Two pools, `reasoning` and `screening`, each a list of named endpoints read from the
  environment. One provider key can serve several endpoints (`N_PROVIDER`).
- `PooledClient` rotates the starting endpoint per call, fails over on transient errors only
  (429, timeout, connection failure, 5xx), rests an endpoint after 429, and caps attempts.
  Permanent errors (auth, bad request) are returned at once.
- Output is validated against Pydantic schemas. One repair attempt, then `LLMOutputInvalid`;
  the caller applies the rule floor from the spec.
- Plain httpx against `/chat/completions` instead of a vendor SDK: one wire format for all
  providers and exact control over failure classification and over what reaches logs.

## Consequences

- Different endpoints may disagree in style. Evaluation must report results per endpoint as
  well as for the pool.
- JSON mode support differs per host; `N_JSON_MODE` selects `json_schema`, `json_object` or
  `none`, and the probe decides which one each endpoint gets.
