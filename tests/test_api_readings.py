"""Reading endpoint tests."""

from fastapi.testclient import TestClient


class TestMeterReadings:
    def test_get_readings(self, client: TestClient):
        # Get a meter ID
        list_response = client.get("/api/v1/meters?limit=1")
        meter_id = list_response.json()["items"][0]["mrid"]

        response = client.get(f"/api/v1/meters/{meter_id}/readings")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] > 0

    def test_get_readings_with_reading_type_filter(self, client: TestClient):
        list_response = client.get("/api/v1/meters?limit=1")
        meter_id = list_response.json()["items"][0]["mrid"]

        response = client.get(
            f"/api/v1/meters/{meter_id}/readings?reading_type_mrid=rt-forward-energy-wh"
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["reading_type_mrid"] == "rt-forward-energy-wh"

    def test_get_readings_validated_only(self, client: TestClient):
        list_response = client.get("/api/v1/meters?limit=1")
        meter_id = list_response.json()["items"][0]["mrid"]

        response = client.get(
            f"/api/v1/meters/{meter_id}/readings?validated_only=true"
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_validated"] is True

    def test_get_readings_meter_not_found(self, client: TestClient):
        response = client.get("/api/v1/meters/nonexistent/readings")
        assert response.status_code == 404


class TestIntervalBlocks:
    def test_get_interval_blocks(self, client: TestClient):
        response = client.get("/api/v1/interval-blocks?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] > 0

    def test_get_interval_blocks_with_meter_filter(self, client: TestClient):
        list_response = client.get("/api/v1/meters?limit=1")
        meter_id = list_response.json()["items"][0]["mrid"]

        response = client.get(f"/api/v1/interval-blocks?meter_mrids={meter_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0

    def test_get_interval_blocks_with_reading_type(self, client: TestClient):
        response = client.get(
            "/api/v1/interval-blocks?reading_type_mrid=rt-voltage-v&limit=1"
        )
        assert response.status_code == 200
        data = response.json()
        if data["total"] > 0:
            assert data["items"][0]["reading_type_mrid"] == "rt-voltage-v"
