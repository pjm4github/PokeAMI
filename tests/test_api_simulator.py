"""Tests for the simulator control plane endpoints."""

from tests.conftest import TEST_API_KEY


def test_simulator_status_no_auth(unauth_client):
    """GET /api/v1/simulator/status is accessible without auth."""
    response = unauth_client.get("/api/v1/simulator/status")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data
    assert "events" in data
    # All components should start enabled
    for name, enabled in data["components"].items():
        assert enabled is True, f"{name} should be enabled"


def test_stop_requires_auth(unauth_client):
    """POST /api/v1/simulator/{component}/stop requires API key."""
    response = unauth_client.post("/api/v1/simulator/headend/stop")
    assert response.status_code == 401


def test_start_requires_auth(unauth_client):
    """POST /api/v1/simulator/{component}/start requires API key."""
    response = unauth_client.post("/api/v1/simulator/headend/start")
    assert response.status_code == 401


def test_stop_and_start_component(client):
    """Stop and start a component, verify status changes."""
    # Stop headend
    r = client.post("/api/v1/simulator/headend/stop")
    assert r.status_code == 200
    assert r.json()["enabled"] is False

    # Verify via status
    status = client.get("/api/v1/simulator/status").json()
    assert status["components"]["headend"] is False

    # Start it back
    r = client.post("/api/v1/simulator/headend/start")
    assert r.status_code == 200
    assert r.json()["enabled"] is True

    # Verify restored
    status = client.get("/api/v1/simulator/status").json()
    assert status["components"]["headend"] is True


def test_invalid_component_returns_404(client):
    """Unknown component name returns 404."""
    r = client.post("/api/v1/simulator/nonexistent/stop")
    assert r.status_code == 404


def test_comm_network_controllable(client):
    """comm_network appears in status and can be stopped/started."""
    # Verify it appears in status
    status = client.get("/api/v1/simulator/status").json()
    assert "comm_network" in status["components"]
    assert status["components"]["comm_network"] is True

    # Stop it
    r = client.post("/api/v1/simulator/comm_network/stop")
    assert r.status_code == 200
    assert r.json()["enabled"] is False

    # Verify via status
    status = client.get("/api/v1/simulator/status").json()
    assert status["components"]["comm_network"] is False

    # Start it back
    r = client.post("/api/v1/simulator/comm_network/start")
    assert r.status_code == 200
    assert r.json()["enabled"] is True


def test_events_logged_on_stop_start(client):
    """Stop/start actions produce event log entries."""
    client.post("/api/v1/simulator/mdm/stop")
    client.post("/api/v1/simulator/mdm/start")
    status = client.get("/api/v1/simulator/status").json()
    events = status["events"]
    mdm_events = [e for e in events if e["component"] == "mdm"]
    assert len(mdm_events) >= 2
    messages = [e["message"] for e in mdm_events]
    assert "mdm stopped" in messages
    assert "mdm started" in messages
