"""Communication network simulation for AMI meter-to-HES data transport.

Models the latency and failure characteristics of different communication
pathways used in Landis+Gyr AMI deployments.

Communication latency model:
    - Cellular LTE: 3-8s (fastest, most reliable, 5% failure rate)
    - RF Mesh: 8-20s (medium, multi-hop delays, 10% failure rate)
    - PLC: 12-25s (slowest, noisy channel, 15% failure rate)
    - COMM_FAILURE meters: 80% failure rate regardless of comm type

References:
    - Landis+Gyr AMI Communication Pathway Selection Guide (publicly available)
    - Landis+Gyr Gridstream HES on-demand read workflow
    - IEC 61968-9:2024, Section 9 "Message Exchanges" (async request patterns)
"""

import random

from app.models.enums import CommunicationType, MeterStatus
from app.models.meter import Meter

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


class CommNetwork:
    """Simulates the communication network between the HES and field meters.

    Determines transmission latency and success/failure for on-demand read
    requests routed through the AMI communication infrastructure.

    References:
        - Landis+Gyr AMI Communication Pathway Selection Guide
        - IEC 61968-9:2024, communication pathway concepts
    """

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()
        self._enabled: bool = True

    def start(self) -> None:
        self._enabled = True

    def stop(self) -> None:
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def simulate_transmission(
        self, meter: Meter
    ) -> tuple[float, bool, str | None]:
        """Simulate network traversal for a single meter.

        Routes the on-demand read request through the meter's communication
        pathway and determines latency and success/failure.

        Args:
            meter: The target meter to communicate with.

        Returns:
            Tuple of (latency_seconds, will_fail, failure_reason).
        """
        if not self._enabled:
            return (0.0, True, "Communication network is disabled")

        comm_type = meter.comm_module.comm_type
        lo, hi = COMM_LATENCY.get(comm_type, (8.0, 20.0))
        latency = self._rng.uniform(lo, hi)

        if meter.status == MeterStatus.COMM_FAILURE:
            will_fail = self._rng.random() < COMM_FAILURE_METER_RATE
        else:
            base_rate = COMM_FAILURE_RATE.get(comm_type, 0.10)
            will_fail = self._rng.random() < base_rate

        failure_reason = self._rng.choice(FAILURE_REASONS) if will_fail else None

        return latency, will_fail, failure_reason
