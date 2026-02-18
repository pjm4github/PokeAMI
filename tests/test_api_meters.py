"""Meter endpoint integration tests."""

from fastapi.testclient import TestClient


class TestListMeters:
    def test_list_meters_success(self, client: TestClient):
        response = client.get("/api/v1/meters")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] == 5

    def test_pagination(self, client: TestClient):
        response = client.get("/api/v1/meters?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_pagination_offset(self, client: TestClient):
        response = client.get("/api/v1/meters?limit=2&offset=4")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1  # Only 1 left at offset 4 of 5

    def test_filter_by_status(self, client: TestClient):
        response = client.get("/api/v1/meters?status=active")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "active"

    def test_filter_by_meter_type(self, client: TestClient):
        response = client.get("/api/v1/meters?meter_type=E350")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["meter_type"] == "E350"


class TestGetMeter:
    def test_get_meter_by_id(self, client: TestClient):
        # First get a meter ID from the list
        list_response = client.get("/api/v1/meters?limit=1")
        meter_id = list_response.json()["items"][0]["mrid"]

        response = client.get(f"/api/v1/meters/{meter_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["mrid"] == meter_id

    def test_get_meter_not_found(self, client: TestClient):
        response = client.get("/api/v1/meters/nonexistent-id")
        assert response.status_code == 404
