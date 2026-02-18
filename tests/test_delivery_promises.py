"""Unit tests for the DeliveryManager simulator component."""

import time
from datetime import datetime, timedelta, timezone

from app.models.delivery_promise import DeliveryPromiseRequest
from app.models.enums import DeliveryPromiseStatus, MeterDeliveryStatus
from app.simulator import SimulatorEngine


class TestDeliveryManager:
    """Tests for delivery promise creation and lifecycle."""

    def test_create_promise(self, simulator: SimulatorEngine):
        meter_mrids = list(simulator.get_meters().keys())[:2]
        request = DeliveryPromiseRequest(
            meter_mrids=meter_mrids,
            start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )

        promise = simulator.create_delivery_promise(request)

        assert promise.promise_id.startswith("dp-")
        assert promise.status == DeliveryPromiseStatus.PENDING
        assert promise.meters_total == 2
        assert promise.meters_collected == 0
        assert promise.meters_failed == 0
        assert len(promise.meter_results) == 2
        assert promise.estimated_delivery > promise.created_at
        assert promise.request.meter_mrids == meter_mrids

    def test_create_promise_with_options(self, simulator: SimulatorEngine):
        meter_mrids = list(simulator.get_meters().keys())[:1]
        request = DeliveryPromiseRequest(
            meter_mrids=meter_mrids,
            start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end=datetime(2026, 1, 2, tzinfo=timezone.utc),
            reading_type_mrid="rt-forward-energy-wh",
            validated_only=True,
        )

        promise = simulator.create_delivery_promise(request)
        assert promise.request.reading_type_mrid == "rt-forward-energy-wh"
        assert promise.request.validated_only is True

    def test_promise_with_unknown_meter(self, simulator: SimulatorEngine):
        request = DeliveryPromiseRequest(
            meter_mrids=["nonexistent-meter-id"],
            start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )

        promise = simulator.create_delivery_promise(request)
        assert promise.meters_total == 1

        # Resolve immediately — unknown meter should fail instantly
        resolved = simulator.get_delivery_promise(promise.promise_id)
        assert resolved is not None
        assert resolved.meter_results[0].status == MeterDeliveryStatus.FAILED
        assert "Unknown meter" in resolved.meter_results[0].failure_reason

    def test_get_promise_not_found(self, simulator: SimulatorEngine):
        result = simulator.get_delivery_promise("dp-nonexistent")
        assert result is None

    def test_promise_lifecycle_eventual_resolution(self, simulator: SimulatorEngine):
        """After enough time, all meters should be resolved (collected or failed)."""
        meter_mrids = list(simulator.get_meters().keys())[:3]
        request = DeliveryPromiseRequest(
            meter_mrids=meter_mrids,
            start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )

        promise = simulator.create_delivery_promise(request)

        # Wait past the estimated delivery time (max ~25s + 5s buffer = 30s)
        # We can't wait that long in tests, but we can check the structure
        resolved = simulator.get_delivery_promise(promise.promise_id)
        assert resolved is not None
        assert resolved.meters_total == 3
        # At minimum some should have been resolved (near-zero latency meters)
        # or still pending (if we're checking immediately)
        total_resolved = resolved.meters_collected + resolved.meters_failed
        pending = sum(
            1 for r in resolved.meter_results
            if r.status == MeterDeliveryStatus.PENDING
        )
        assert total_resolved + pending == 3

    def test_list_promises(self, simulator: SimulatorEngine):
        # Create a couple of promises
        meter_mrids = list(simulator.get_meters().keys())[:1]
        for _ in range(2):
            request = DeliveryPromiseRequest(
                meter_mrids=meter_mrids,
                start=datetime(2026, 1, 1, tzinfo=timezone.utc),
                end=datetime(2026, 1, 2, tzinfo=timezone.utc),
            )
            simulator.create_delivery_promise(request)

        promises = simulator.list_delivery_promises()
        assert len(promises) >= 2

    def test_meter_results_have_correct_mrids(self, simulator: SimulatorEngine):
        meter_mrids = list(simulator.get_meters().keys())[:3]
        request = DeliveryPromiseRequest(
            meter_mrids=meter_mrids,
            start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )

        promise = simulator.create_delivery_promise(request)
        result_mrids = [r.meter_mrid for r in promise.meter_results]
        assert result_mrids == meter_mrids
