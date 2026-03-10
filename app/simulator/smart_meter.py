"""SmartMeter — wraps a Meter with its ReadingSource to model an emulated device.

A SmartMeter represents a physical meter in the field that can produce readings
on request.  It delegates actual data generation to a pluggable ReadingSource
(e.g. DataGenerator today, LoadModel in the future).

References:
    - Landis+Gyr E350/E360/S4x/E660 meter families
    - IEC 61968-9:2024, EndDevice model
"""

from datetime import datetime

from app.models.meter import Meter
from app.models.reading import MeterReading
from app.simulator.reading_source import ReadingSource


class SmartMeter:
    """An emulated smart meter that produces readings via a ReadingSource."""

    def __init__(
        self, meter: Meter, is_solar: bool, reading_source: ReadingSource
    ):
        self._meter = meter
        self._is_solar = is_solar
        self._reading_source = reading_source

    @property
    def meter(self) -> Meter:
        return self._meter

    @property
    def mrid(self) -> str:
        return self._meter.mrid

    @property
    def is_solar(self) -> bool:
        return self._is_solar

    @property
    def reading_source(self) -> ReadingSource:
        return self._reading_source

    @reading_source.setter
    def reading_source(self, value: ReadingSource) -> None:
        self._reading_source = value

    def read(self, data_days: int, interval_minutes: int) -> list[MeterReading]:
        """Produce historical interval readings for this meter."""
        return self._reading_source.generate_meter_readings(
            self._meter, self._is_solar, data_days, interval_minutes
        )

    def read_on_demand(
        self,
        start: datetime,
        end: datetime,
        interval_minutes: int = 15,
        reading_type_mrid: str | None = None,
    ) -> list[MeterReading]:
        """Produce a fresh on-demand reading for a specific time range."""
        return self._reading_source.generate_on_demand_readings(
            meter=self._meter,
            is_solar=self._is_solar,
            start=start,
            end=end,
            interval_minutes=interval_minutes,
            reading_type_mrid=reading_type_mrid,
        )
