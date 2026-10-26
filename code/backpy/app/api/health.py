from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict:
    """Service status and which model endpoints are configured. No keys, no live call."""
    muse = request.app.state.muse
    openweights = request.app.state.openweights
    return {
        "status": "ok",
        "replay_mode": request.app.state.settings.replay_mode,
        "models": {
            "reasoning": muse.describe(),
            "screening": openweights.describe(),
        },
    }
