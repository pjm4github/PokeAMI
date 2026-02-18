"""Tests for the dashboard route."""

import pytest
from fastapi.testclient import TestClient

from app.dashboard_app import create_dashboard_app


@pytest.fixture(scope="module")
def dashboard_client() -> TestClient:
    """Test client for the standalone dashboard app."""
    app = create_dashboard_app()
    return TestClient(app)


def test_dashboard_returns_html(dashboard_client):
    """GET /dashboard returns 200 with HTML content, no auth required."""
    response = dashboard_client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_dashboard_contains_key_markers(dashboard_client):
    """Dashboard HTML contains essential UI markers."""
    response = dashboard_client.get("/dashboard")
    body = response.text
    assert "PokeAMI" in body
    assert "pollStatus" in body
    assert "apiKey" in body


def test_dashboard_no_auth_required(dashboard_client):
    """Dashboard is accessible without an API key."""
    response = dashboard_client.get("/dashboard")
    assert response.status_code == 200


def test_dashboard_api_base_injected(dashboard_client):
    """Dashboard HTML has the API base URL injected (not the placeholder)."""
    response = dashboard_client.get("/dashboard")
    body = response.text
    assert "{{API_BASE}}" not in body
    assert "http://localhost:8000/api/v1" in body
