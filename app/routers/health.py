"""Health check endpoint (no authentication required)."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(request: Request) -> dict:
    """Health check endpoint returning system status.

    No authentication required. Returns meter count and system status.
    """
    simulator = request.app.state.simulator
    return {
        "status": "healthy",
        "meter_count": simulator.meter_count,
        "version": "1.0.0",
    }
