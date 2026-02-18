"""End-to-end scenario tests.

Tests complete user flows through the API.
"""

from fastapi.testclient import TestClient


class TestMeterReadingFlow:
    """E2E: List meters → Get readings → Verify interval data."""

    def test_full_meter_reading_flow(self, client: TestClient):
        # Step 1: List meters
        meters_resp = client.get("/api/v1/meters")
        assert meters_resp.status_code == 200
        meters = meters_resp.json()
        assert meters["total"] > 0

        # Step 2: Pick first meter and get its readings
        meter_id = meters["items"][0]["mrid"]
        readings_resp = client.get(f"/api/v1/meters/{meter_id}/readings")
        assert readings_resp.status_code == 200
        readings = readings_resp.json()
        assert readings["total"] > 0

        # Step 3: Verify readings have interval blocks with data
        first_reading = readings["items"][0]
        assert first_reading["meter_mrid"] == meter_id
        assert len(first_reading["interval_blocks"]) > 0
        block = first_reading["interval_blocks"][0]
        assert len(block["interval_readings"]) > 0

        # Step 4: Verify interval reading structure
        interval = block["interval_readings"][0]
        assert "timestamp" in interval
        assert "value" in interval
        assert isinstance(interval["value"], (int, float))


class TestUsagePointFlow:
    """E2E: List usage points → Get point → Get readings."""

    def test_full_usage_point_flow(self, client: TestClient):
        # Step 1: List usage points
        up_resp = client.get("/api/v1/usage-points")
        assert up_resp.status_code == 200
        usage_points = up_resp.json()
        assert usage_points["total"] > 0

        # Step 2: Get specific usage point
        up_id = usage_points["items"][0]["mrid"]
        detail_resp = client.get(f"/api/v1/usage-points/{up_id}")
        assert detail_resp.status_code == 200
        up_detail = detail_resp.json()
        assert up_detail["mrid"] == up_id
        assert len(up_detail["meter_mrids"]) > 0

        # Step 3: Get readings for the usage point
        readings_resp = client.get(f"/api/v1/usage-points/{up_id}/meter-readings")
        assert readings_resp.status_code == 200
        assert readings_resp.json()["total"] > 0


class TestAnalyticsFlow:
    """E2E: Check analytics endpoints return consistent data."""

    def test_analytics_consistency(self, client: TestClient):
        # Get a meter
        meters = client.get("/api/v1/meters?limit=1").json()
        meter_id = meters["items"][0]["mrid"]

        # Get demand and voltage summaries for that meter
        demand = client.get(
            f"/api/v1/analytics/demand-summary?meter_mrid={meter_id}"
        )
        assert demand.status_code == 200
        demand_data = demand.json()
        assert len(demand_data) == 1

        voltage = client.get(
            f"/api/v1/analytics/voltage-summary?meter_mrid={meter_id}"
        )
        assert voltage.status_code == 200
        voltage_data = voltage.json()
        assert len(voltage_data) == 1

        # Demand should be positive
        assert demand_data[0]["peak_demand_w"] > 0
        # Voltage should be in a reasonable range
        assert voltage_data[0]["average_voltage_v"] > 100


class TestReadingTypeFlow:
    """E2E: Get reading types → Use to filter readings."""

    def test_reading_type_filter_flow(self, client: TestClient):
        # Step 1: Get reading types
        rt_resp = client.get("/api/v1/reading-types")
        assert rt_resp.status_code == 200
        reading_types = rt_resp.json()
        assert reading_types["total"] > 0

        # Step 2: Pick a reading type
        rt_mrid = reading_types["items"][0]["mrid"]

        # Step 3: Use it to filter meter readings
        meters = client.get("/api/v1/meters?limit=1").json()
        meter_id = meters["items"][0]["mrid"]

        readings = client.get(
            f"/api/v1/meters/{meter_id}/readings?reading_type_mrid={rt_mrid}"
        )
        assert readings.status_code == 200
        data = readings.json()
        for item in data["items"]:
            assert item["reading_type_mrid"] == rt_mrid
