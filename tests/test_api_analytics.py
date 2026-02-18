"""Analytics endpoint tests."""

from fastapi.testclient import TestClient


class TestDemandSummary:
    def test_get_demand_summary(self, client: TestClient):
        response = client.get("/api/v1/analytics/demand-summary")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_demand_summary_single_meter(self, client: TestClient):
        # Get a meter ID
        meters = client.get("/api/v1/meters?limit=1").json()
        meter_id = meters["items"][0]["mrid"]

        response = client.get(
            f"/api/v1/analytics/demand-summary?meter_mrid={meter_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["meter_mrid"] == meter_id

    def test_demand_summary_fields(self, client: TestClient):
        response = client.get("/api/v1/analytics/demand-summary")
        data = response.json()

        for summary in data:
            assert "peak_demand_w" in summary
            assert "average_demand_w" in summary
            assert "min_demand_w" in summary
            assert "load_factor" in summary
            assert 0.0 <= summary["load_factor"] <= 1.0


class TestVoltageSummary:
    def test_get_voltage_summary(self, client: TestClient):
        response = client.get("/api/v1/analytics/voltage-summary")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_voltage_summary_fields(self, client: TestClient):
        response = client.get("/api/v1/analytics/voltage-summary")
        data = response.json()

        for summary in data:
            assert "average_voltage_v" in summary
            assert "max_voltage_v" in summary
            assert "min_voltage_v" in summary
            assert "ansi_c84_1_exceedance_count" in summary
            assert summary["min_voltage_v"] <= summary["average_voltage_v"]
            assert summary["average_voltage_v"] <= summary["max_voltage_v"]


class TestRevenueProtectionAlerts:
    def test_get_alerts(self, client: TestClient):
        response = client.get("/api/v1/analytics/revenue-protection-alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
