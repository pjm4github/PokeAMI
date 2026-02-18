"""SimulatorEngine facade - wires all simulator components together.

Architecture:
    MeterPark → DataGenerator → Headend → MDM → AnalyticsEngine

References:
    - Landis+Gyr AMI architecture: Meters → HES → MDM → Analytics
    - IEC 61968-9:2024, AMI system architecture
"""

import random

from app.models.meter import Meter
from app.models.reading import MeterReading, ReadingType
from app.models.usage_point import UsagePoint
from app.models.analytics import DemandSummary, RevenueProtectionAlert, VoltageSummary
from app.models.delivery_promise import DeliveryPromise, DeliveryPromiseRequest
from app.simulator.analytics_engine import AnalyticsEngine
from app.simulator.data_generator import DataGenerator
from app.simulator.delivery_manager import DeliveryManager
from app.simulator.headend import Headend
from app.simulator.mdm import MDM
from app.simulator.meter_park import MeterPark

from datetime import datetime


class SimulatorEngine:
    """Facade that wires all simulator components.

    Components:
        - MeterPark: Fleet generation and management
        - DataGenerator: Realistic time-series generation
        - Headend: Simulated Gridstream HES (raw data collection)
        - MDM: Meter Data Management with VEE pipeline
        - AnalyticsEngine: Demand, voltage, and revenue protection analytics

    References:
        - Landis+Gyr Gridstream platform architecture
        - IEC 61968-9:2024, AMI system architecture
    """

    def __init__(
        self,
        meter_count: int = 50,
        data_days: int = 30,
        interval_minutes: int = 15,
        seed: int | None = None,
    ):
        self._meter_count = meter_count
        self._data_days = data_days
        self._interval_minutes = interval_minutes
        self._seed = seed

        rng = random.Random(seed) if seed is not None else random.Random()

        self._meter_park = MeterPark(meter_count, rng)
        self._data_generator = DataGenerator(rng)
        self._headend = Headend(self._meter_park, self._data_generator)
        self._mdm = MDM(self._headend)
        self._analytics = AnalyticsEngine(self._headend)
        self._delivery_manager = DeliveryManager(rng)

    def initialize(self) -> None:
        """Generate all simulated data.

        This triggers the full data generation pipeline:
        1. MeterPark already created in __init__ (meters + usage points)
        2. Headend generates raw readings via DataGenerator
        """
        self._headend.initialize(self._data_days, self._interval_minutes)

    # --- Meter access ---

    def get_meters(self) -> dict[str, Meter]:
        return self._headend.get_meters()

    def get_meter(self, mrid: str) -> Meter | None:
        return self._headend.get_meter(mrid)

    # --- Usage point access ---

    def get_usage_points(self) -> dict[str, UsagePoint]:
        return self._headend.get_usage_points()

    def get_usage_point(self, mrid: str) -> UsagePoint | None:
        return self._headend.get_usage_point(mrid)

    def get_meters_for_usage_point(self, usage_point_mrid: str) -> list[Meter]:
        return self._headend.get_meters_for_usage_point(usage_point_mrid)

    # --- Reading access ---

    def get_meter_readings(
        self,
        meter_mrid: str,
        start: datetime | None = None,
        end: datetime | None = None,
        reading_type_mrid: str | None = None,
        validated_only: bool = False,
    ) -> list[MeterReading]:
        """Get meter readings, optionally VEE-validated."""
        if validated_only:
            return self._mdm.get_validated_readings(
                meter_mrid, start, end, reading_type_mrid
            )
        return self._headend.get_meter_readings(
            meter_mrid, start, end, reading_type_mrid
        )

    def get_reading_types(self) -> dict[str, ReadingType]:
        return self._headend.get_reading_types()

    # --- Analytics access ---

    def get_demand_summary(
        self,
        start: datetime,
        end: datetime,
        meter_mrid: str | None = None,
    ) -> list[DemandSummary]:
        return self._analytics.get_demand_summary(start, end, meter_mrid)

    def get_voltage_summary(
        self,
        start: datetime,
        end: datetime,
        meter_mrid: str | None = None,
    ) -> list[VoltageSummary]:
        return self._analytics.get_voltage_summary(start, end, meter_mrid)

    def get_revenue_protection_alerts(
        self,
        start: datetime,
        end: datetime,
    ) -> list[RevenueProtectionAlert]:
        return self._analytics.get_revenue_protection_alerts(start, end)

    def get_billing_determinants(
        self,
        meter_mrid: str,
        start: datetime,
        end: datetime,
    ) -> dict:
        return self._mdm.get_billing_determinants(meter_mrid, start, end)

    # --- Delivery promise access ---

    def create_delivery_promise(
        self, request: DeliveryPromiseRequest
    ) -> DeliveryPromise:
        """Create a new asynchronous delivery promise for on-demand reads."""
        return self._delivery_manager.create_promise(
            request=request,
            meters=self.get_meters(),
            get_readings_fn=self.get_meter_readings,
        )

    def get_delivery_promise(self, promise_id: str) -> DeliveryPromise | None:
        """Retrieve and resolve a delivery promise by ID."""
        return self._delivery_manager.get_promise(promise_id)

    def list_delivery_promises(self) -> list[DeliveryPromise]:
        """List all delivery promises."""
        return self._delivery_manager.list_promises()

    @property
    def meter_count(self) -> int:
        return len(self._headend.get_meters())

    @property
    def headend(self) -> Headend:
        return self._headend

    @property
    def mdm(self) -> MDM:
        return self._mdm

    @property
    def analytics(self) -> AnalyticsEngine:
        return self._analytics
