"""Usage point endpoint tests."""

from fastapi.testclient import TestClient


class TestListUsagePoints:
    def test_list_usage_points(self, client: TestClient):
        response = client.get("/api/v1/usage-points")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5

    def test_filter_by_connection_state(self, client: TestClient):
        response = client.get("/api/v1/usage-points?connection_state=connected")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["connection_state"] == "connected"


class TestGetUsagePoint:
    def test_get_usage_point_by_id(self, client: TestClient):
        list_response = client.get("/api/v1/usage-points?limit=1")
        up_id = list_response.json()["items"][0]["mrid"]

        response = client.get(f"/api/v1/usage-points/{up_id}")
        assert response.status_code == 200
        assert response.json()["mrid"] == up_id

    def test_get_usage_point_not_found(self, client: TestClient):
        response = client.get("/api/v1/usage-points/nonexistent-id")
        assert response.status_code == 404


class TestUsagePointReadings:
    def test_get_readings_for_usage_point(self, client: TestClient):
        list_response = client.get("/api/v1/usage-points?limit=1")
        up_id = list_response.json()["items"][0]["mrid"]

        response = client.get(f"/api/v1/usage-points/{up_id}/meter-readings")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0

    def test_readings_not_found_usage_point(self, client: TestClient):
        response = client.get("/api/v1/usage-points/nonexistent/meter-readings")
        assert response.status_code == 404
