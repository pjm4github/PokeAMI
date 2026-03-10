"""LoadModel stub — future physics-based ReadingSource.

Placeholder for a physics-based load simulation that would replace or
complement DataGenerator.  Intended to model thermal dynamics, occupancy
patterns, weather data, and appliance-level disaggregation to produce
realistic meter readings grounded in physical principles rather than
statistical curves.

Not yet implemented — all data methods raise NotImplementedError.

References:
    - EnergyPlus building simulation (DOE)
    - CEUS / RECS load profile databases
    - IEC 61968-9:2024, Section 6.3 "Meter Reading Model"
"""

from datetime import datetime

from app.models.meter import Meter
from app.models.reading import MeterReading, ReadingType


class LoadModel:
    """Physics-based reading source (stub — not yet implemented).

    Future implementation would accept weather data, building parameters,
    and occupancy schedules to produce physically-grounded interval readings.
    """

    def __init__(self) -> None:
        self._enabled: bool = True

    def start(self) -> None:
        self._enabled = True

    def stop(self) -> None:
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def generate_meter_readings(
        self,
        meter: Meter,
        is_solar: bool,
        data_days: int,
        interval_minutes: int,
    ) -> list[MeterReading]:
        raise NotImplementedError(
            "LoadModel is a stub — physics-based generation is not yet implemented. "
            "Use DataGenerator as the ReadingSource for now."
        )

    def generate_on_demand_readings(
        self,
        meter: Meter,
        is_solar: bool,
        start: datetime,
        end: datetime,
        interval_minutes: int = 15,
        reading_type_mrid: str | None = None,
    ) -> list[MeterReading]:
        raise NotImplementedError(
            "LoadModel is a stub — physics-based generation is not yet implemented. "
            "Use DataGenerator as the ReadingSource for now."
        )

    def get_reading_types(self) -> dict[str, ReadingType]:
        raise NotImplementedError(
            "LoadModel is a stub — reading type catalog is not yet implemented. "
            "Use DataGenerator as the ReadingSource for now."
        )

    def get_reading_type_mrids_for_meter(
        self, meter: Meter, is_solar: bool
    ) -> list[str]:
        raise NotImplementedError(
            "LoadModel is a stub — reading type selection is not yet implemented. "
            "Use DataGenerator as the ReadingSource for now."
        )
