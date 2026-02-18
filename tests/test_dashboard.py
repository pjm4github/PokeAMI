"""Tests for the dashboard route."""


def test_dashboard_returns_html(unauth_client):
    """GET /dashboard returns 200 with HTML content, no auth required."""
    response = unauth_client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_dashboard_contains_key_markers(unauth_client):
    """Dashboard HTML contains essential UI markers."""
    response = unauth_client.get("/dashboard")
    body = response.text
    assert "PokeAMI" in body
    assert "pollStatus" in body
    assert "apiKey" in body


def test_dashboard_no_auth_required(unauth_client):
    """Dashboard is accessible without an API key."""
    response = unauth_client.get("/dashboard")
    assert response.status_code == 200
