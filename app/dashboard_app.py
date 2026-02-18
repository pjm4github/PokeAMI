"""Standalone FastAPI app for the PokeAMI dashboard.

Runs on a separate port from the main API and proxies API calls
via the browser (CORS enabled on the API server).
"""

from fastapi import FastAPI

from app.config import get_settings
from app.routers import dashboard


def create_dashboard_app() -> FastAPI:
    """Create the dashboard-only FastAPI application."""
    settings = get_settings()
    api_base = f"http://localhost:{settings.port}/api/v1"

    app = FastAPI(title="PokeAMI Dashboard", docs_url=None, redoc_url=None)
    app.state.api_base = api_base
    app.include_router(dashboard.router)

    return app


dashboard_app = create_dashboard_app()
