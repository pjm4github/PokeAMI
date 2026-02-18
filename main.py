"""Entry point for the Meter API application.

Usage:
    python main.py

Starts the API server and the dashboard server on separate ports.
"""

import threading

import uvicorn

from app.config import get_settings


def main() -> None:
    """Run both the API server and the dashboard server."""
    settings = get_settings()

    # Run the dashboard on its own port in a background thread
    dashboard_server = uvicorn.Server(
        uvicorn.Config(
            "app.dashboard_app:dashboard_app",
            host=settings.host,
            port=settings.dashboard_port,
            log_level="warning",
        )
    )
    dashboard_thread = threading.Thread(target=dashboard_server.run, daemon=True)
    dashboard_thread.start()

    # Run the main API on the foreground thread
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
