"""ReadingSource protocol — pluggable data source interface for smart meters.

Defines the contract that any reading source (DataGenerator, future LoadModel,
etc.) must satisfy to supply interval readings to SmartMeter instances.

References:
    - IEC 61968-9:2024, Section 6.3 "Meter Reading Model"
    - Strategy pattern (GoF) for swappable data generation backends
"""

from datetime import datetime
from typing import Protocol, runtime_checkable

from app.models.meter import Meter
from app.models.reading import MeterReading, ReadingType


@runtime_checkable
class ReadingSource(Protocol):
    """Protocol for pluggable meter reading data sources.

    Any class that implements these methods can serve as the data backend
    for SmartMeter instances.  DataGenerator satisfies this protocol today;
    a future LoadModel (physics-based simulation) will as well.
    """

    def generate_meter_readings(
        self,
        meter: Meter,
        is_solar: bool,
        data_days: int,
        interval_minutes: int,
    ) -> list[MeterReading]: ...

    def generate_on_demand_readings(
        self,
        meter: Meter,
        is_solar: bool,
        start: datetime,
        end: datetime,
        interval_minutes: int,
        reading_type_mrid: str | None = None,
    ) -> list[MeterReading]: ...

    def get_reading_types(self) -> dict[str, ReadingType]: ...

    def get_reading_type_mrids_for_meter(
        self, meter: Meter, is_solar: bool
    ) -> list[str]: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def is_enabled(self) -> bool: ...
