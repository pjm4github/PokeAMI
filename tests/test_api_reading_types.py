"""Reading type endpoint tests."""

from fastapi.testclient import TestClient


class TestReadingTypes:
    def test_list_reading_types(self, client: TestClient):
        response = client.get("/api/v1/reading-types")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    def test_reading_types_have_valid_enums(self, client: TestClient):
        response = client.get("/api/v1/reading-types")
        data = response.json()

        valid_units = {"Wh", "W", "V", "A", "VA", "VAr", "Hz", "none"}
        valid_flow = {"forward", "reverse", "net", "total", "none"}

        for rt in data["items"]:
            assert rt["unit"] in valid_units
            assert rt["flow_direction"] in valid_flow
            assert rt["mrid"]
            assert rt["name"]

    def test_reading_types_contain_expected(self, client: TestClient):
        response = client.get("/api/v1/reading-types")
        data = response.json()
        mrids = [rt["mrid"] for rt in data["items"]]

        assert "rt-forward-energy-wh" in mrids
        assert "rt-demand-w" in mrids
        assert "rt-voltage-v" in mrids
