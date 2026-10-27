"""Muse Voice Transcribe: a WAV clip to a transcript (dev.meta.ai/docs/api-reference/voice).

A voice note in an already-risky chat is turned into text here, the transcript is masked
by the same rules as any message, then assessed. The audio is processed in memory and
never written to the database or a log. The audio does reach Meta's ASR for transcription;
that is stated in the consent text and the README, since it differs from text, which is
masked on the phone before anything leaves.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from app.config import Endpoint, Settings, endpoint_from_env
from app.llm.base import LLMError, PermanentLLMError, TransientLLMError

log = logging.getLogger("dcai.voice")

_TRANSIENT_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 529}


class VoiceUnavailable(LLMError):
    """Transcription could not be done; the caller decides what the level should be."""


@dataclass(frozen=True)
class Transcript:
    text: str
    audio_seconds: float
    cost_usd: float | None


class VoiceClient:
    """Calls POST /v1/asr/transcribe. Built from an existing endpoint's base and key (the
    'meta' pool endpoint by default), so one key serves chat and voice."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        price_per_hour: float | None,
        http: httpx.AsyncClient,
    ):
        self._url = base_url.rstrip("/") + "/asr/transcribe"
        self._key = api_key
        self._model = model
        self._price_per_hour = price_per_hour
        self._http = http

    async def transcribe(self, audio_wav: bytes, *, timeout: float = 60.0) -> Transcript:
        request = {"model": self._model, "audioEncoding": "WAV", "mode": "PUSH_TO_TALK"}
        files = {
            "request": (None, json.dumps(request), "application/json"),
            "audio": ("note.wav", audio_wav, "audio/wav"),
        }
        try:
            resp = await self._http.post(
                self._url,
                files=files,
                headers={"Authorization": f"Bearer {self._key}", "Accept": "application/json"},
                timeout=timeout,
            )
        except httpx.TimeoutException as exc:
            raise TransientLLMError(f"voice timeout after {timeout}s") from exc
        except httpx.TransportError as exc:
            raise TransientLLMError(f"voice connection failed: {type(exc).__name__}") from exc

        if resp.status_code in _TRANSIENT_STATUS:
            raise TransientLLMError(f"voice HTTP {resp.status_code}", status=resp.status_code)
        if resp.status_code >= 400:
            # Error type only; a provider message could echo content.
            raise PermanentLLMError(f"voice HTTP {resp.status_code}")
        try:
            data = resp.json()
            text = data["transcript"]
            audio_seconds = float(data.get("audioDurationMs") or 0) / 1000.0
        except (ValueError, KeyError, TypeError) as exc:
            raise TransientLLMError("voice response is not a transcript") from exc

        cost = None
        if self._price_per_hour is not None:
            cost = self._price_per_hour * audio_seconds / 3600.0
        log.info(
            "voice_transcribe model=%s audio_seconds=%.1f chars=%d cost_usd=%s",
            self._model,
            audio_seconds,
            len(text),
            "unknown" if cost is None else f"{cost:.6f}",
        )
        return Transcript(text=text, audio_seconds=audio_seconds, cost_usd=cost)


def build_voice_client(settings: Settings, http: httpx.AsyncClient) -> VoiceClient | None:
    """A voice client from the configured endpoint, or None when voice is not configured."""
    if not settings.voice_endpoint:
        return None
    endpoint: Endpoint | None = endpoint_from_env(settings.voice_endpoint)
    if endpoint is None:
        return None
    return VoiceClient(
        base_url=endpoint.base_url,
        api_key=endpoint.api_key,
        model=settings.voice_model,
        price_per_hour=settings.voice_price_per_hour,
        http=http,
    )
