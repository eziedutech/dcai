"""POST /v1/ask: Ask dcAI. Nothing of the question or the answer is stored."""

from fastapi import APIRouter, HTTPException, Request, status

from app.analysis.service import state_item
from app.api.deps import DbDep, GuardianDep
from app.ask.assistant import AskIn, AskOut, ask
from app.ratelimit import RateLimiter

router = APIRouter(tags=["ask"])

# Each question costs up to five Muse Spark turns.
QUESTIONS_PER_MINUTE = 6


@router.post("/ask")
async def ask_dcai(body: AskIn, request: Request, db: DbDep, guardian: GuardianDep) -> AskOut:
    limiter = state_item(
        request.app.state, "ask_limiter", lambda: RateLimiter(QUESTIONS_PER_MINUTE)
    )
    if not limiter.allow(guardian.id):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "too many questions", headers={"Retry-After": "60"}
        )
    result = await ask(request.app.state.muse, db, guardian, body)
    return result.out
