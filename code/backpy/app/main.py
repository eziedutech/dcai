"""FastAPI entry point."""

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.api.ask import router as ask_router
from app.api.auth import router as auth_router
from app.api.children import router as children_router
from app.api.dashboard import router as dashboard_router
from app.api.devices import device_router, guardian_router
from app.api.health import router as health_router
from app.api.messages import router as messages_router
from app.config import get_settings
from app.llm import build_clients


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # httpx logs request URLs at INFO; keep them out, they add nothing and grow the log.
    logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    http = httpx.AsyncClient()
    app.state.settings = settings
    app.state.muse, app.state.openweights = build_clients(settings, http)
    try:
        yield
    finally:
        queued = getattr(app.state, "worker", None)
        if queued is not None:
            await queued.idle()  # finish messages already accepted before closing clients
        await http.aclose()


app = FastAPI(title="Digital Safe dcAI", version="0.1.0", lifespan=lifespan)
app.include_router(health_router, prefix="/v1")
app.include_router(auth_router, prefix="/v1")
app.include_router(children_router, prefix="/v1")
app.include_router(messages_router, prefix="/v1")
app.include_router(guardian_router, prefix="/v1")
app.include_router(device_router, prefix="/v1")
app.include_router(dashboard_router, prefix="/v1")
app.include_router(ask_router, prefix="/v1")
