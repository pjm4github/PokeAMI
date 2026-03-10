"""Simulated Landis+Gyr Gridstream Head-End System (HES).

The HES is the central data collection system that communicates with field
devices (meters) and collects raw meter reading data. This simulation stores
raw (un-validated) readings keyed by meter mRID.

Reading generation is delegated to MeterPark (which in turn delegates to
each SmartMeter's ReadingSource), keeping the HES free of any direct
dependency on DataGenerator.

References:
    - Landis+Gyr Gridstream HES Product Description (publicly available)
    - Landis+Gyr Gridstream platform documentation (publicly available)
    - IEC 61968-9:2024, Head-End System role in AMI architecture
    - DLMS/COSEM (IEC 62056) - Meter data exchange protocol concepts
"""

from datetime import datetime

from app.models.meter import Meter
from app.models.reading import MeterReading, ReadingType
from app.models.usage_point import UsagePoint
from app.simulator.meter_park import MeterPark


class Headend:
    """Simulated Gridstream Head-End System.

    Manages meter inventory via MeterPark and collects raw data by asking
    each SmartMeter to read through its ReadingSource. Stores un-validated
    MeterReading objects keyed by meter_mrid.

    References:
        - Landis+Gyr Gridstream HES Product Description
        - IEC 61968-9:2024, AMI system architecture
    """

    def __init__(self, meter_park: MeterPark):
        self._meter_park = meter_park
        # Raw readings: meter_mrid -> list[MeterReading]
        self._readings: dict[str, list[MeterReading]] = {}
        self._enabled: bool = True

    def start(self) -> None:
        self._enabled = True

    def stop(self) -> None:
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def meter_park(self) -> MeterPark:
        """Access the managed meter park."""
        return self._meter_park

    def initialize(self, data_days: int, interval_minutes: int) -> None:
        """Generate full dataset for all meters.

        Args:
            data_days: Number of days of historical data to generate.
            interval_minutes: Interval between readings in minutes.
        """
        for mrid in self._meter_park.meters:
            readings = self._meter_park.read_meter(mrid, data_days, interval_minutes)
            self._readings[mrid] = readings

    def get_meters(self) -> dict[str, Meter]:
        """Return all meters in the fleet."""
        if not self._enabled:
            return {}
        return self._meter_park.meters

    def get_meter(self, mrid: str) -> Meter | None:
        """Get a specific meter by mRID."""
        return self._meter_park.get_meter(mrid)

    def get_usage_points(self) -> dict[str, UsagePoint]:
        """Return all usage points."""
        return self._meter_park.usage_points

    def get_usage_point(self, mrid: str) -> UsagePoint | None:
        """Get a specific usage point by mRID."""
        return self._meter_park.get_usage_point(mrid)

    def get_meters_for_usage_point(self, usage_point_mrid: str) -> list[Meter]:
        """Get meters associated with a usage point."""
        return self._meter_park.get_meters_for_usage_point(usage_point_mrid)

    def get_meter_readings(
        self,
        meter_mrid: str,
        start: datetime | None = None,
        end: datetime | None = None,
        reading_type_mrid: str | None = None,
    ) -> list[MeterReading]:
        """Query raw meter readings with optional filtering.

        Args:
            meter_mrid: Meter to query readings for.
            start: Optional start of time range filter.
            end: Optional end of time range filter.
            reading_type_mrid: Optional reading type filter.

        Returns:
            Filtered list of MeterReading objects (un-validated).
        """
        if not self._enabled:
            return []
        readings = self._readings.get(meter_mrid, [])

        if reading_type_mrid:
            readings = [r for r in readings if r.reading_type_mrid == reading_type_mrid]

        if start or end:
            filtered = []
            for reading in readings:
                # Filter interval blocks' readings by time range
                new_blocks = []
                for block in reading.interval_blocks:
                    filtered_intervals = [
                        ir for ir in block.interval_readings
                        if (start is None or ir.timestamp >= start)
                        and (end is None or ir.timestamp <= end)
                    ]
                    if filtered_intervals:
                        new_block = block.model_copy(update={
                            "interval_readings": filtered_intervals,
                        })
                        new_blocks.append(new_block)
                if new_blocks:
                    new_reading = reading.model_copy(update={
                        "interval_blocks": new_blocks,
                    })
                    filtered.append(new_reading)
            readings = filtered

        return readings

    def collect_on_demand_reading(
        self,
        meter_mrid: str,
        start: datetime | None = None,
        end: datetime | None = None,
        reading_type_mrid: str | None = None,
        interval_minutes: int = 15,
    ) -> list[MeterReading]:
        """Collect a fresh on-demand reading from a meter via the comm network.

        Unlike get_meter_readings() which returns pre-stored startup data,
        this method asks the SmartMeter (through MeterPark) to produce fresh
        readings for the requested time range — simulating the HES receiving
        new data from the meter through the communication network.

        The returned readings are NOT stored in self._readings; they represent
        a one-time on-demand collection.

        Args:
            meter_mrid: Meter to collect from.
            start: Start of the requested time range.
            end: End of the requested time range.
            reading_type_mrid: Optional reading type filter.
            interval_minutes: Interval between readings in minutes.

        Returns:
            List of fresh (un-validated) MeterReading objects.
        """
        if not self._enabled:
            return []

        return self._meter_park.read_meter_on_demand(
            mrid=meter_mrid,
            start=start,
            end=end,
            interval_minutes=interval_minutes,
            reading_type_mrid=reading_type_mrid,
        )

    def get_all_readings_for_meter(self, meter_mrid: str) -> list[MeterReading]:
        """Get all raw readings for a meter (no filtering)."""
        if not self._enabled:
            return []
        return self._readings.get(meter_mrid, [])

    def get_reading_types(self) -> dict[str, ReadingType]:
        """Return the catalog of available reading types."""
        return self._meter_park.get_reading_types()
