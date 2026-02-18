"""FastAPI application factory with lifespan-managed simulator.

References:
    - FastAPI lifespan events documentation
    - IEC 61968-9:2024, AMI system architecture
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
from app.routers import analytics, delivery_promises, health, meters, reading_types, readings, usage_points
from app.simulator import SimulatorEngine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan: initialize simulator on startup."""
    settings = get_settings()
    simulator = SimulatorEngine(
        meter_count=settings.meter_count,
        data_days=settings.data_days,
        interval_minutes=settings.interval_minutes,
    )
    simulator.initialize()
    app.state.simulator = simulator

    host = settings.host
    port = settings.port
    # Use localhost for display when bound to all interfaces
    display_host = "localhost" if host == "0.0.0.0" else host
    base = f"http://{display_host}:{port}"

    logger.info("")
    logger.info("=" * 60)
    logger.info("  Meter API for Headend")
    logger.info("  Simulating %d meters, %d days of %d-min data",
                settings.meter_count, settings.data_days, settings.interval_minutes)
    logger.info("-" * 60)
    logger.info("  Swagger UI:   %s/docs", base)
    logger.info("  ReDoc:        %s/redoc", base)
    logger.info("  OpenAPI JSON: %s/openapi.json", base)
    logger.info("  Health check: %s/api/v1/health", base)
    logger.info("=" * 60)
    logger.info("")

    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Meter API for Headend",
        description=(
            "CIM-compatible OpenAPI interface to simulated Landis+Gyr AMI "
            "(Advanced Metering Infrastructure). Provides access to meter "
            "readings, usage points, and analytics from simulated Gridstream "
            "HES, MDM, and Analytics components.\n\n"
            "Data models follow IEC 61968-9:2024 CIM standards.\n\n"
            "Authentication: Include `X-API-Key` header on all requests "
            "(except /health)."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # Register routers
    prefix = "/api/v1"
    app.include_router(health.router, prefix=prefix)
    app.include_router(meters.router, prefix=prefix)
    app.include_router(readings.router, prefix=prefix)
    app.include_router(usage_points.router, prefix=prefix)
    app.include_router(reading_types.router, prefix=prefix)
    app.include_router(analytics.router, prefix=prefix)
    app.include_router(delivery_promises.router, prefix=prefix)

    return app


app = create_app()
