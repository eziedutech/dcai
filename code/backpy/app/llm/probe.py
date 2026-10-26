"""Day 1 probe: prove each configured endpoint answers, using synthetic text only.

    python -m app.llm.probe models fireworks [filter]   list model IDs from a provider
    python -m app.llm.probe call                        one structured call per endpoint

`models` reads <PROVIDER>_BASE and <PROVIDER>_API_KEY. `call` costs one small request per
endpoint; run it once, not in a loop.
"""

import asyncio
import os
import sys

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.llm import LLMError, PooledClient
from app.main import configure_logging


class ProbeAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: str = Field(pattern="^(aman|perhatian)$")
    reason: str = Field(max_length=120)


SYSTEM = "Kamu menilai satu pesan sintetis untuk uji koneksi. Jawab singkat."
USER = 'Pesan sintetis: "Besok main bola di lapangan sekolah jam 4 ya." Nilai levelnya.'


async def list_models(provider: str, needle: str) -> int:
    prefix = provider.upper().replace("-", "_")
    base, key = os.environ.get(f"{prefix}_BASE", ""), os.environ.get(f"{prefix}_API_KEY", "")
    if prefix == "META":  # spec variable names
        base = base or os.environ.get("META_API_BASE", "https://api.meta.ai/v1")
    if not (base and key):
        print(f"{prefix}_BASE and {prefix}_API_KEY must be set")
        return 2
    async with httpx.AsyncClient() as http:
        resp = await http.get(
            f"{base.rstrip('/')}/models", headers={"Authorization": f"Bearer {key}"}, timeout=20
        )
    print(f"GET {base.rstrip('/')}/models -> HTTP {resp.status_code}")
    if resp.status_code != 200:
        return 1
    ids = sorted(m.get("id", "") for m in resp.json().get("data", []))
    shown = [i for i in ids if needle.lower() in i.lower()]
    print(f"{len(ids)} models, {len(shown)} matching {needle!r}:")
    for model_id in shown:
        print(f"  {model_id}")
    return 0


async def call_each() -> int:
    configure_logging()
    settings = get_settings()
    failures = 0
    async with httpx.AsyncClient() as http:
        for pool in ("reasoning", "screening"):
            endpoints = settings.endpoints(pool)
            if not endpoints:
                print(f"[{pool}] no endpoint configured")
                continue
            for ep in endpoints:
                client = PooledClient(
                    [ep], http=http, timeout=settings.llm_timeout_seconds, max_transient_retries=0
                )
                try:
                    r = await client.complete_json(
                        purpose=f"probe_{pool}",
                        system=SYSTEM,
                        user=USER,
                        schema=ProbeAnswer,
                        max_tokens=1500,
                    )
                except LLMError as exc:
                    failures += 1
                    print(f"[{pool}] {ep.name} {ep.model}: FAILED {type(exc).__name__}: {exc}")
                    continue
                u = r.usage
                cost = "unknown" if u.cost_usd is None else f"{u.cost_usd:.6f}"
                print(
                    f"[{pool}] {ep.name} {ep.model}: OK level={r.value.level} "
                    f"attempts={len(r.attempts)} in={u.tokens_in} cached={u.tokens_cached} "
                    f"out={u.tokens_out} latency_ms={u.latency_ms} cost_usd={cost}"
                )
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    get_settings()  # loads .env into the environment
    if len(argv) >= 2 and argv[0] == "models":
        return asyncio.run(list_models(argv[1], argv[2] if len(argv) > 2 else ""))
    if argv == ["call"]:
        return asyncio.run(call_each())
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
