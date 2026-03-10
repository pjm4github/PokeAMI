"""Meter fleet generation and management.

Generates a realistic distribution of Landis+Gyr meters with associated
usage points, communication modules, and realistic configuration.

Each meter is wrapped in a SmartMeter that delegates data generation to a
pluggable ReadingSource (DataGenerator today, LoadModel in the future).

References:
    - Landis+Gyr E350 Brochure (publicly available) - Residential basic meter
    - Landis+Gyr E360 LTE Technical Data (publicly available) - Residential advanced
    - Landis+Gyr E650 S4x Product Specifications (publicly available) - C&I polyphase
    - Landis+Gyr E660/Revelo IoT Grid Sensing Platform (publicly available) - C&I IoT
    - Landis+Gyr AMI Communication Pathway Selection Guide (publicly available)
"""

import random
from datetime import datetime, timedelta, timezone

from app.models.common import generate_mrid
from app.models.enums import (
    CommunicationType,
    ConnectionState,
    MeterStatus,
    MeterType,
    PhaseCode,
)
from app.models.meter import CommModule, Meter
from app.models.reading import MeterReading, ReadingType
from app.models.usage_point import UsagePoint
from app.simulator.reading_source import ReadingSource
from app.simulator.smart_meter import SmartMeter

# Meter type distribution (weighted)
# Ref: Typical utility fleet composition per L+G deployment guides
METER_TYPE_WEIGHTS: list[tuple[MeterType, float]] = [
    (MeterType.E350, 0.40),        # 40% residential basic
    (MeterType.E360, 0.30),        # 30% residential advanced
    (MeterType.S4X_E650, 0.20),    # 20% C&I polyphase
    (MeterType.E660_REVELO, 0.10), # 10% C&I IoT
]

# Meter configuration per type
# Ref: L+G product datasheets (publicly available)
METER_CONFIGS: dict[MeterType, dict] = {
    MeterType.E350: {
        "model": "E350",
        "serial_prefix": "E350",
        "firmware_versions": ["7.3.1", "7.3.2", "7.4.0"],
        "comm_types": [CommunicationType.RF_MESH, CommunicationType.PLC],
        "phase_code": PhaseCode.AN,
        "rated_power_w": 9600.0,  # 80A × 120V
        "form_number": "2S",
        "rated_voltage_v": 120.0,
        "service_category": "residential",
    },
    MeterType.E360: {
        "model": "E360",
        "serial_prefix": "E360",
        "firmware_versions": ["2.1.0", "2.2.0", "2.3.1"],
        "comm_types": [CommunicationType.CELLULAR_LTE, CommunicationType.RF_MESH],
        "phase_code": PhaseCode.AN,
        "rated_power_w": 24000.0,  # 200A × 120V
        "form_number": "2S",
        "rated_voltage_v": 120.0,
        "service_category": "residential",
    },
    MeterType.S4X_E650: {
        "model": "S4x/E650",
        "serial_prefix": "S4X",
        "firmware_versions": ["5.1.0", "5.2.0", "5.3.0"],
        "comm_types": [CommunicationType.CELLULAR_LTE, CommunicationType.RF_MESH],
        "phase_code": PhaseCode.ABCN,
        "rated_power_w": 96000.0,  # 400A × 240V
        "form_number": "9S",
        "rated_voltage_v": 240.0,
        "service_category": "commercial",
    },
    MeterType.E660_REVELO: {
        "model": "E660/Revelo",
        "serial_prefix": "E660",
        "firmware_versions": ["1.0.0", "1.1.0", "1.2.0"],
        "comm_types": [CommunicationType.CELLULAR_LTE],
        "phase_code": PhaseCode.ABCN,
        "rated_power_w": 192000.0,  # 800A × 240V
        "form_number": "16S",
        "rated_voltage_v": 240.0,
        "service_category": "industrial",
    },
}

# Sample street names for generating realistic addresses
STREET_NAMES = [
    "Oak", "Maple", "Cedar", "Pine", "Elm", "Birch", "Walnut", "Ash",
    "Main", "First", "Second", "Third", "Park", "Lake", "River", "Hill",
    "Spring", "Meadow", "Forest", "Valley", "Summit", "Ridge", "Creek", "Brook",
]

STREET_TYPES = ["St", "Ave", "Blvd", "Dr", "Ln", "Way", "Ct", "Pl"]

COMM_FIRMWARE_VERSIONS = {
    CommunicationType.RF_MESH: ["3.2.1", "3.3.0", "3.4.0"],
    CommunicationType.PLC: ["2.0.1", "2.1.0"],
    CommunicationType.CELLULAR_LTE: ["4.1.0", "4.2.0", "4.3.0"],
}


class MeterPark:
    """Manages a fleet of emulated smart meters and their associated usage points.

    Each meter is wrapped in a SmartMeter that delegates reading generation
    to the supplied ReadingSource (DataGenerator, future LoadModel, etc.).

    References:
        - Typical utility AMI deployment fleet composition
        - Landis+Gyr product documentation for meter specifications
    """

    def __init__(
        self,
        meter_count: int,
        reading_source: ReadingSource,
        rng: random.Random | None = None,
    ):
        self._reading_source = reading_source
        self._rng = rng or random.Random()
        self._smart_meters: dict[str, SmartMeter] = {}
        self._usage_points: dict[str, UsagePoint] = {}
        self._enabled: bool = True
        self._generate_fleet(meter_count)

    def start(self) -> None:
        self._enabled = True

    def stop(self) -> None:
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def _generate_fleet(self, count: int) -> None:
        """Generate the meter fleet with realistic distribution."""
        types = [t for t, _ in METER_TYPE_WEIGHTS]
        weights = [w for _, w in METER_TYPE_WEIGHTS]

        for i in range(count):
            meter_type = self._rng.choices(types, weights=weights, k=1)[0]
            meter, usage_point = self._create_meter(i, meter_type)
            is_solar = hash(meter.serial_number) % 5 == 0
            smart_meter = SmartMeter(meter, is_solar, self._reading_source)
            self._smart_meters[meter.mrid] = smart_meter
            self._usage_points[usage_point.mrid] = usage_point

    def _create_meter(self, index: int, meter_type: MeterType) -> tuple[Meter, UsagePoint]:
        """Create a single meter with associated usage point."""
        config = METER_CONFIGS[meter_type]
        meter_mrid = generate_mrid()
        up_mrid = generate_mrid()

        # Generate serial number with model-specific prefix
        serial = f"{config['serial_prefix']}-{100000 + index:06d}"

        # Generate comm module
        comm_type = self._rng.choice(config["comm_types"])
        comm_fw = self._rng.choice(COMM_FIRMWARE_VERSIONS[comm_type])
        mac = ":".join(f"{self._rng.randint(0, 255):02x}" for _ in range(6))

        now = datetime.now(timezone.utc)
        install_date = now - timedelta(days=self._rng.randint(30, 1825))  # 1 month to 5 years ago

        # ~5% COMM_FAILURE, ~3% MAINTENANCE, rest ACTIVE
        status_roll = self._rng.random()
        if status_roll < 0.05:
            status = MeterStatus.COMM_FAILURE
        elif status_roll < 0.08:
            status = MeterStatus.MAINTENANCE
        else:
            status = MeterStatus.ACTIVE

        # Last communication depends on status
        if status == MeterStatus.COMM_FAILURE:
            last_comm = now - timedelta(hours=self._rng.randint(24, 168))
        else:
            last_comm = now - timedelta(minutes=self._rng.randint(1, 60))

        signal_strength = self._rng.uniform(-85.0, -45.0)
        if status == MeterStatus.COMM_FAILURE:
            signal_strength = self._rng.uniform(-100.0, -90.0)

        comm_module = CommModule(
            comm_type=comm_type,
            firmware_version=comm_fw,
            mac_address=mac,
            signal_strength=round(signal_strength, 1),
            last_communication=last_comm,
        )

        meter = Meter(
            mrid=meter_mrid,
            serial_number=serial,
            manufacturer="Landis+Gyr",
            model=config["model"],
            firmware_version=self._rng.choice(config["firmware_versions"]),
            status=status,
            connection_state=ConnectionState.CONNECTED,
            install_date=install_date,
            phase_code=config["phase_code"],
            comm_module=comm_module,
            usage_point_mrid=up_mrid,
            meter_type=meter_type,
            rated_power_w=config["rated_power_w"],
            ct_ratio=1.0 if meter_type in (MeterType.E350, MeterType.E360) else 200.0,
            form_number=config["form_number"],
            demand_interval_minutes=15,
        )

        # Generate address
        street_num = self._rng.randint(100, 9999)
        street_name = self._rng.choice(STREET_NAMES)
        street_type = self._rng.choice(STREET_TYPES)
        address = f"{street_num} {street_name} {street_type}"

        usage_point = UsagePoint(
            mrid=up_mrid,
            name=f"UP-{serial}",
            connection_state=ConnectionState.CONNECTED,
            phase_code=config["phase_code"],
            rated_power_w=config["rated_power_w"],
            rated_voltage_v=config["rated_voltage_v"],
            service_category=config["service_category"],
            meter_mrids=[meter_mrid],
            service_location_address=address,
            customer_account_id=f"ACCT-{10000 + index:06d}",
        )

        return meter, usage_point

    @property
    def meters(self) -> dict[str, Meter]:
        """All meters keyed by mRID (backward-compatible view)."""
        if not self._enabled:
            return {}
        return {mrid: sm.meter for mrid, sm in self._smart_meters.items()}

    @property
    def smart_meters(self) -> dict[str, SmartMeter]:
        """All SmartMeter instances keyed by mRID."""
        if not self._enabled:
            return {}
        return self._smart_meters

    @property
    def usage_points(self) -> dict[str, UsagePoint]:
        """All usage points keyed by mRID."""
        if not self._enabled:
            return {}
        return self._usage_points

    def get_meter(self, mrid: str) -> Meter | None:
        """Get a meter by mRID."""
        sm = self._smart_meters.get(mrid)
        return sm.meter if sm else None

    def get_usage_point(self, mrid: str) -> UsagePoint | None:
        """Get a usage point by mRID."""
        return self._usage_points.get(mrid)

    def get_meters_for_usage_point(self, usage_point_mrid: str) -> list[Meter]:
        """Get all meters associated with a usage point."""
        up = self._usage_points.get(usage_point_mrid)
        if not up:
            return []
        return [
            self._smart_meters[m].meter
            for m in up.meter_mrids
            if m in self._smart_meters
        ]

    def is_solar_meter(self, meter: Meter) -> bool:
        """Determine if a meter has solar/reverse energy generation.

        ~20% of residential meters are assigned solar capability.
        """
        sm = self._smart_meters.get(meter.mrid)
        if sm:
            return sm.is_solar
        # Fallback for meters not in our fleet
        return hash(meter.serial_number) % 5 == 0

    def read_meter(
        self, mrid: str, data_days: int, interval_minutes: int
    ) -> list[MeterReading]:
        """Ask a SmartMeter to produce historical readings."""
        sm = self._smart_meters.get(mrid)
        if sm is None:
            return []
        return sm.read(data_days, interval_minutes)

    def read_meter_on_demand(
        self,
        mrid: str,
        start: datetime,
        end: datetime,
        interval_minutes: int = 15,
        reading_type_mrid: str | None = None,
    ) -> list[MeterReading]:
        """Ask a SmartMeter to produce a fresh on-demand reading."""
        sm = self._smart_meters.get(mrid)
        if sm is None:
            return []
        return sm.read_on_demand(start, end, interval_minutes, reading_type_mrid)

    def get_reading_types(self) -> dict[str, ReadingType]:
        """Delegate to the reading source for the reading type catalog."""
        return self._reading_source.get_reading_types()
