"""Session-scoped test fixtures for the Meter API test suite.

Uses a small dataset (5 meters, 3 days) for fast test execution.
"""

import os

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.simulator import SimulatorEngine

TEST_API_KEY = "test-api-key-12345"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test settings with small dataset for fast execution."""
    os.environ["API_KEY"] = TEST_API_KEY
    os.environ["METER_COUNT"] = "5"
    os.environ["DATA_DAYS"] = "3"
    os.environ["INTERVAL_MINUTES"] = "15"
    return Settings(
        api_key=TEST_API_KEY,
        meter_count=5,
        data_days=3,
        interval_minutes=15,
    )


@pytest.fixture(scope="session")
def simulator(test_settings: Settings) -> SimulatorEngine:
    """Pre-initialized simulator with deterministic seed."""
    sim = SimulatorEngine(
        meter_count=test_settings.meter_count,
        data_days=test_settings.data_days,
        interval_minutes=test_settings.interval_minutes,
        seed=42,
    )
    sim.initialize()
    return sim


@pytest.fixture(scope="session")
def app(simulator: SimulatorEngine):
    """FastAPI app with pre-initialized simulator."""
    application = create_app()
    application.state.simulator = simulator
    return application


@pytest.fixture(scope="session")
def client(app) -> TestClient:
    """Test client with valid API key."""
    return TestClient(app, headers={"X-API-Key": TEST_API_KEY})


@pytest.fixture(scope="session")
def unauth_client(app) -> TestClient:
    """Test client without API key."""
    return TestClient(app)
