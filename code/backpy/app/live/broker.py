"""Live updates over Server-Sent Events.

Keys are "device:<id>" (the child's phone: nudges, conversation levels, config changes)
and "child:<id>" (the guardian's dashboard: events and assessments). Payloads carry
levels, labels and Coach output, never message text.

Each key keeps its last events in memory, so a client that reconnects with Last-Event-ID
gets what it missed. One process only: with several workers this needs a shared bus
(PostgreSQL LISTEN/NOTIFY), noted for deployment. A restart starts a new id prefix, and
a client holding an id from before the restart gets the whole buffer.
"""

import asyncio
import json
import secrets
from collections import deque
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

BUFFER_PER_KEY = 100
MAX_KEYS = 5000


@dataclass(frozen=True)
class LiveEvent:
    seq: int
    event: str
    data: dict

    def encode(self, boot: str) -> str:
        payload = json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
        return f"id: {boot}-{self.seq}\nevent: {self.event}\ndata: {payload}\n\n"


class Broker:
    def __init__(self, buffer: int = BUFFER_PER_KEY):
        self.boot = secrets.token_hex(4)
        self._seq = 0
        self._buffer = buffer
        self._history: dict[str, deque[LiveEvent]] = {}
        self._subscribers: dict[str, set[asyncio.Queue[LiveEvent]]] = {}

    def publish(self, key: str, event: str, data: dict) -> LiveEvent:
        self._seq += 1
        item = LiveEvent(self._seq, event, data)
        history = self._history.pop(key, None) or deque(maxlen=self._buffer)
        history.append(item)
        self._history[key] = history  # re-inserted: dict order is least recent first
        while len(self._history) > MAX_KEYS:
            self._history.pop(next(iter(self._history)))
        for queue in self._subscribers.get(key, ()):
            queue.put_nowait(item)
        return item

    def since(self, key: str, last_event_id: str | None) -> list[LiveEvent]:
        history = list(self._history.get(key, ()))
        if not last_event_id:
            return []
        boot, _, seq = last_event_id.partition("-")
        if boot != self.boot or not seq.isdigit():
            return history
        return [e for e in history if e.seq > int(seq)]

    def subscribe(self, key: str) -> asyncio.Queue[LiveEvent]:
        queue: asyncio.Queue[LiveEvent] = asyncio.Queue()
        self._subscribers.setdefault(key, set()).add(queue)
        return queue

    def unsubscribe(self, key: str, queue: asyncio.Queue[LiveEvent]) -> None:
        subs = self._subscribers.get(key)
        if subs is not None:
            subs.discard(queue)
            if not subs:
                del self._subscribers[key]

    def subscriber_count(self, key: str) -> int:
        return len(self._subscribers.get(key, ()))


async def sse_stream(
    broker: Broker,
    key: str,
    last_event_id: str | None,
    *,
    heartbeat: float,
    max_seconds: float,
    is_disconnected: Callable[[], Awaitable[bool]] | None = None,
) -> AsyncIterator[str]:
    """Missed events first, then live ones, a comment line as heartbeat, and a close after
    max_seconds so clients reconnect (and re-authenticate) regularly."""
    queue = broker.subscribe(key)
    loop = asyncio.get_running_loop()
    deadline = loop.time() + max_seconds
    try:
        yield "retry: 3000\n\n"
        last = 0
        for item in broker.since(key, last_event_id):
            last = item.seq
            yield item.encode(broker.boot)
        while (remaining := deadline - loop.time()) > 0:
            if is_disconnected is not None and await is_disconnected():
                return
            try:
                item = await asyncio.wait_for(queue.get(), timeout=min(heartbeat, remaining))
            except TimeoutError:
                yield ": ping\n\n"
                continue
            if item.seq > last:
                yield item.encode(broker.boot)
    finally:
        broker.unsubscribe(key, queue)


def device_key(device_id) -> str:
    return f"device:{device_id}"


def child_key(child_id) -> str:
    return f"child:{child_id}"
