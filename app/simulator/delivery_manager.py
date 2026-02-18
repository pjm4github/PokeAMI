"""Delivery Manager - simulates asynchronous on-demand meter read collection.

Simulates the slow/unreliable communication between the HES and field meters
by assigning each meter a simulated collection time based on its communication
type and operational status.

Communication latency model:
    - Cellular LTE: 3-8s (fastest, most reliable, 5% failure rate)
    - RF Mesh: 8-20s (medium, multi-hop delays, 10% failure rate)
    - PLC: 12-25s (slowest, noisy channel, 15% failure rate)
    - COMM_FAILURE meters: 80% failure rate regardless of comm type

References:
    - Landis+Gyr Gridstream HES on-demand read workflow
    - Landis+Gyr AMI Communication Pathway Selection Guide (publicly available)
    - IEC 61968-9:2024, Section 9 "Message Exchanges" (async request patterns)
"""

import random
from datetime import datetime, timedelta, timezone

from app.models.common import generate_mrid
from app.models.delivery_promise import (
    DeliveryPromise,
    DeliveryPromiseRequest,
    MeterDeliveryResult,
)
from app.models.enums import (
    CommunicationType,
    DeliveryPromiseStatus,
    MeterDeliveryStatus,
    MeterStatus,
)
from app.models.meter import Meter
from app.models.reading import MeterReading

# Latency ranges per comm type (seconds)
COMM_LATENCY: dict[CommunicationType, tuple[float, float]] = {
    CommunicationType.CELLULAR_LTE: (3.0, 8.0),
    CommunicationType.RF_MESH: (8.0, 20.0),
    CommunicationType.PLC: (12.0, 25.0),
}

# Base failure rates per comm type
COMM_FAILURE_RATE: dict[CommunicationType, float] = {
    CommunicationType.CELLULAR_LTE: 0.05,
    CommunicationType.RF_MESH: 0.10,
    CommunicationType.PLC: 0.15,
}

# Failure rate override for meters in COMM_FAILURE status
COMM_FAILURE_METER_RATE = 0.80

# Randomly selected failure reasons
FAILURE_REASONS = [
    "Communication timeout — no response from meter after 3 retries",
    "RF Mesh path unavailable — no route to meter",
    "PLC signal degradation — CRC errors exceeded threshold",
    "Meter in maintenance mode — remote read disabled",
    "Cellular network unreachable — SIM registration failed",
]

# Buffer added to estimated delivery beyond the slowest meter
DELIVERY_BUFFER_SECONDS = 5.0


class DeliveryManager:
    """Manages delivery promises for asynchronous on-demand meter reads.

    Each promise tracks per-meter collection timing metadata so that
    on each GET the manager can resolve which meters have "arrived"
    based on wall-clock time vs. simulated collection time.

    References:
        - Landis+Gyr Gridstream HES on-demand read request workflow
        - Landis+Gyr Command Center async job status model
    """

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()
        # promise_id -> DeliveryPromise (latest snapshot)
        self._promises: dict[str, DeliveryPromise] = {}
        # promise_id -> per-meter timing metadata
        # { meter_mrid: { "collection_time": datetime, "will_fail": bool, "failure_reason": str | None } }
        self._timing: dict[str, dict[str, dict]] = {}

    def create_promise(
        self,
        request: DeliveryPromiseRequest,
        meters: dict[str, Meter],
        get_readings_fn,
    ) -> DeliveryPromise:
        """Create a new delivery promise and schedule simulated collection.

        Args:
            request: The client's delivery promise request.
            meters: All known meters keyed by mRID (for looking up comm type / status).
            get_readings_fn: Callable(meter_mrid, start, end, reading_type_mrid, validated_only) -> list[MeterReading]
        """
        now = datetime.now(timezone.utc)
        promise_id = f"dp-{generate_mrid()}"

        timing: dict[str, dict] = {}
        max_collection_seconds = 0.0

        meter_results: list[MeterDeliveryResult] = []
        for mrid in request.meter_mrids:
            meter = meters.get(mrid)

            if meter is None:
                # Unknown meter — immediate failure
                timing[mrid] = {
                    "collection_time": now,
                    "will_fail": True,
                    "failure_reason": f"Unknown meter mRID: {mrid}",
                }
                meter_results.append(
                    MeterDeliveryResult(
                        meter_mrid=mrid,
                        status=MeterDeliveryStatus.PENDING,
                        readings=None,
                        failure_reason=None,
                    )
                )
                continue

            comm_type = meter.comm_module.comm_type
            lo, hi = COMM_LATENCY.get(comm_type, (8.0, 20.0))
            latency = self._rng.uniform(lo, hi)

            # Determine failure
            if meter.status == MeterStatus.COMM_FAILURE:
                will_fail = self._rng.random() < COMM_FAILURE_METER_RATE
            else:
                base_rate = COMM_FAILURE_RATE.get(comm_type, 0.10)
                will_fail = self._rng.random() < base_rate

            failure_reason = self._rng.choice(FAILURE_REASONS) if will_fail else None

            collection_time = now + timedelta(seconds=latency)
            timing[mrid] = {
                "collection_time": collection_time,
                "will_fail": will_fail,
                "failure_reason": failure_reason,
            }

            if latency > max_collection_seconds:
                max_collection_seconds = latency

            meter_results.append(
                MeterDeliveryResult(
                    meter_mrid=mrid,
                    status=MeterDeliveryStatus.PENDING,
                    readings=None,
                    failure_reason=None,
                )
            )

        estimated_delivery = now + timedelta(
            seconds=max_collection_seconds + DELIVERY_BUFFER_SECONDS
        )

        promise = DeliveryPromise(
            promise_id=promise_id,
            status=DeliveryPromiseStatus.PENDING,
            created_at=now,
            estimated_delivery=estimated_delivery,
            request=request,
            meters_total=len(request.meter_mrids),
            meters_collected=0,
            meters_failed=0,
            meter_results=meter_results,
            failure_summary=None,
        )

        self._promises[promise_id] = promise
        self._timing[promise_id] = timing
        # Store the readings callback for later resolution
        self._get_readings_fn = get_readings_fn

        return promise

    def get_promise(self, promise_id: str) -> DeliveryPromise | None:
        """Retrieve and resolve a delivery promise by ID.

        On each call, checks wall-clock time against per-meter simulated
        collection times and updates statuses accordingly.
        """
        promise = self._promises.get(promise_id)
        if promise is None:
            return None

        timing = self._timing[promise_id]
        now = datetime.now(timezone.utc)

        updated_results: list[MeterDeliveryResult] = []
        collected = 0
        failed = 0

        for result in promise.meter_results:
            mrid = result.meter_mrid
            meta = timing[mrid]
            collection_time: datetime = meta["collection_time"]

            if now >= collection_time:
                if meta["will_fail"]:
                    updated_results.append(
                        MeterDeliveryResult(
                            meter_mrid=mrid,
                            status=MeterDeliveryStatus.FAILED,
                            readings=None,
                            failure_reason=meta["failure_reason"],
                        )
                    )
                    failed += 1
                else:
                    # Collect readings from the simulator
                    readings = self._get_readings_fn(
                        mrid,
                        promise.request.start,
                        promise.request.end,
                        promise.request.reading_type_mrid,
                        promise.request.validated_only,
                    )
                    updated_results.append(
                        MeterDeliveryResult(
                            meter_mrid=mrid,
                            status=MeterDeliveryStatus.COLLECTED,
                            readings=readings,
                            failure_reason=None,
                        )
                    )
                    collected += 1
            else:
                # Not yet arrived
                updated_results.append(result)

        # Derive overall status
        total = promise.meters_total
        if collected + failed == total:
            if failed == total:
                status = DeliveryPromiseStatus.FAILED
            elif failed > 0:
                status = DeliveryPromiseStatus.PARTIAL
            else:
                status = DeliveryPromiseStatus.COMPLETED
        elif collected + failed > 0:
            status = DeliveryPromiseStatus.IN_PROGRESS
        else:
            status = DeliveryPromiseStatus.PENDING

        # Build failure summary if any failures
        failure_summary = None
        if failed > 0:
            failure_summary = f"{failed}/{total} meters failed collection"

        updated = DeliveryPromise(
            promise_id=promise.promise_id,
            status=status,
            created_at=promise.created_at,
            estimated_delivery=promise.estimated_delivery,
            request=promise.request,
            meters_total=total,
            meters_collected=collected,
            meters_failed=failed,
            meter_results=updated_results,
            failure_summary=failure_summary,
        )

        self._promises[promise_id] = updated
        return updated

    def list_promises(self) -> list[DeliveryPromise]:
        """List all delivery promises (resolved to current state)."""
        # Resolve each promise to its current state
        return [self.get_promise(pid) for pid in list(self._promises.keys())]
