"""Delivery Promise API integration tests."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient


class TestCreateDeliveryPromise:
    def test_create_promise_success(self, client: TestClient):
        # Get some meter mRIDs first
        meters_resp = client.get("/api/v1/meters?limit=2")
        meter_mrids = [m["mrid"] for m in meters_resp.json()["items"]]

        response = client.post(
            "/api/v1/delivery-promises",
            json={
                "meter_mrids": meter_mrids,
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-02T00:00:00Z",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["promise_id"].startswith("dp-")
        assert data["status"] == "pending"
        assert data["meters_total"] == 2
        assert data["meters_collected"] == 0
        assert data["meters_failed"] == 0
        assert len(data["meter_results"]) == 2
        assert data["request"]["meter_mrids"] == meter_mrids

    def test_create_promise_with_reading_type(self, client: TestClient):
        meters_resp = client.get("/api/v1/meters?limit=1")
        meter_mrids = [m["mrid"] for m in meters_resp.json()["items"]]

        response = client.post(
            "/api/v1/delivery-promises",
            json={
                "meter_mrids": meter_mrids,
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-02T00:00:00Z",
                "reading_type_mrid": "rt-forward-energy-wh",
                "validated_only": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["request"]["reading_type_mrid"] == "rt-forward-energy-wh"
        assert data["request"]["validated_only"] is True

    def test_create_promise_empty_meters_422(self, client: TestClient):
        response = client.post(
            "/api/v1/delivery-promises",
            json={
                "meter_mrids": [],
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-02T00:00:00Z",
            },
        )
        assert response.status_code == 422

    def test_create_promise_start_after_end_422(self, client: TestClient):
        meters_resp = client.get("/api/v1/meters?limit=1")
        meter_mrids = [m["mrid"] for m in meters_resp.json()["items"]]

        response = client.post(
            "/api/v1/delivery-promises",
            json={
                "meter_mrids": meter_mrids,
                "start": "2026-01-15T00:00:00Z",
                "end": "2026-01-01T00:00:00Z",
            },
        )
        assert response.status_code == 422

    def test_create_promise_requires_auth(self, unauth_client: TestClient):
        response = unauth_client.post(
            "/api/v1/delivery-promises",
            json={
                "meter_mrids": ["fake-id"],
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-02T00:00:00Z",
            },
        )
        assert response.status_code in (401, 403)


class TestGetDeliveryPromise:
    def test_get_promise_by_id(self, client: TestClient):
        # Create a promise first
        meters_resp = client.get("/api/v1/meters?limit=2")
        meter_mrids = [m["mrid"] for m in meters_resp.json()["items"]]

        create_resp = client.post(
            "/api/v1/delivery-promises",
            json={
                "meter_mrids": meter_mrids,
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-02T00:00:00Z",
            },
        )
        promise_id = create_resp.json()["promise_id"]

        response = client.get(f"/api/v1/delivery-promises/{promise_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["promise_id"] == promise_id
        assert data["meters_total"] == 2

    def test_get_promise_not_found(self, client: TestClient):
        response = client.get("/api/v1/delivery-promises/dp-nonexistent")
        assert response.status_code == 404

    def test_get_promise_resolves_status(self, client: TestClient):
        """Promise status should reflect per-meter collection state."""
        meters_resp = client.get("/api/v1/meters?limit=1")
        meter_mrids = [m["mrid"] for m in meters_resp.json()["items"]]

        create_resp = client.post(
            "/api/v1/delivery-promises",
            json={
                "meter_mrids": meter_mrids,
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-02T00:00:00Z",
            },
        )
        promise_id = create_resp.json()["promise_id"]

        # Poll the promise — status should be valid
        response = client.get(f"/api/v1/delivery-promises/{promise_id}")
        data = response.json()
        assert data["status"] in ["pending", "inProgress", "completed", "partial", "failed"]

    def test_unknown_meter_fails(self, client: TestClient):
        """A promise with an unknown meter mRID should fail that meter."""
        create_resp = client.post(
            "/api/v1/delivery-promises",
            json={
                "meter_mrids": ["totally-fake-mrid"],
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-02T00:00:00Z",
            },
        )
        promise_id = create_resp.json()["promise_id"]

        response = client.get(f"/api/v1/delivery-promises/{promise_id}")
        data = response.json()
        assert data["meters_failed"] == 1
        assert data["meter_results"][0]["status"] == "failed"
        assert "Unknown meter" in data["meter_results"][0]["failure_reason"]


class TestListDeliveryPromises:
    def test_list_promises(self, client: TestClient):
        response = client.get("/api/v1/delivery-promises")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_promises_pagination(self, client: TestClient):
        response = client.get("/api/v1/delivery-promises?limit=1&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1
        assert data["offset"] == 0
        assert len(data["items"]) <= 1
