"""Authentication tests."""

from fastapi.testclient import TestClient


class TestAuthentication:
    def test_missing_api_key_returns_401(self, unauth_client: TestClient):
        response = unauth_client.get("/api/v1/meters")
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    def test_wrong_api_key_returns_401(self, app):
        client = TestClient(app, headers={"X-API-Key": "wrong-key"})
        response = client.get("/api/v1/meters")
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_health_no_auth_required(self, unauth_client: TestClient):
        response = unauth_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_valid_api_key_succeeds(self, client: TestClient):
        response = client.get("/api/v1/meters")
        assert response.status_code == 200
