"""Entry point for the Meter API application.

Usage:
    python main.py

Starts the uvicorn server with settings from environment variables or .env file.
"""

import uvicorn

from app.config import get_settings


def main() -> None:
    """Run the application server."""
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
