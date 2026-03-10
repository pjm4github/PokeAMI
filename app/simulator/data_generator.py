"""Realistic time-series data generation for simulated meter readings.

Generates 15-minute interval data with realistic load curves, seasonal patterns,
quality injection, and meter-type-specific behavior.

References:
    - IEC 61968-9:2024, Section 6.3 "Meter Reading Model"
    - Typical residential and C&I load profiles (utility industry standard curves)
    - Landis+Gyr meter specifications for value ranges
    - ANSI C84.1 voltage ranges (114V-126V for 120V nominal)
"""

import math
import random
from datetime import datetime, timedelta, timezone

from app.models.common import DateTimeInterval, generate_mrid
from app.models.enums import (
    AccumulationKind,
    CommodityKind,
    FlowDirectionKind,
    MeasurementKind,
    MeterType,
    PhaseCode,
    ReadingQualityType,
    UnitSymbol,
)
from app.models.meter import Meter
from app.models.reading import (
    IntervalBlock,
    IntervalReading,
    MeterReading,
    ReadingQuality,
    ReadingType,
)


# Predefined reading types catalog
# Ref: IEC 61968-9:2024, ReadingType 18-attribute coded structure
# Ref: PNNL-34946, Section 4.3 "ReadingType Structure"
READING_TYPES: dict[str, ReadingType] = {}

_FORWARD_ENERGY_MRID = "rt-forward-energy-wh"
_REVERSE_ENERGY_MRID = "rt-reverse-energy-wh"
_DEMAND_MRID = "rt-demand-w"
_VOLTAGE_MRID = "rt-voltage-v"

READING_TYPES[_FORWARD_ENERGY_MRID] = ReadingType(
    mrid=_FORWARD_ENERGY_MRID,
    name="Forward Active Energy (Wh)",
    accumulation=AccumulationKind.DELTA_DATA,
    flow_direction=FlowDirectionKind.FORWARD,
    commodity=CommodityKind.ELECTRICITY_SECONDARY_METERED,
    measurement_kind=MeasurementKind.ENERGY,
    unit=UnitSymbol.WH,
    phase=PhaseCode.NONE,
    measuring_period_minutes=15,
    multiplier=1.0,
)

READING_TYPES[_REVERSE_ENERGY_MRID] = ReadingType(
    mrid=_REVERSE_ENERGY_MRID,
    name="Reverse Active Energy (Wh)",
    accumulation=AccumulationKind.DELTA_DATA,
    flow_direction=FlowDirectionKind.REVERSE,
    commodity=CommodityKind.ELECTRICITY_SECONDARY_METERED,
    measurement_kind=MeasurementKind.ENERGY,
    unit=UnitSymbol.WH,
    phase=PhaseCode.NONE,
    measuring_period_minutes=15,
    multiplier=1.0,
)

READING_TYPES[_DEMAND_MRID] = ReadingType(
    mrid=_DEMAND_MRID,
    name="Demand (W)",
    accumulation=AccumulationKind.INSTANTANEOUS,
    flow_direction=FlowDirectionKind.FORWARD,
    commodity=CommodityKind.ELECTRICITY_SECONDARY_METERED,
    measurement_kind=MeasurementKind.DEMAND,
    unit=UnitSymbol.W,
    phase=PhaseCode.NONE,
    measuring_period_minutes=15,
    multiplier=1.0,
)

READING_TYPES[_VOLTAGE_MRID] = ReadingType(
    mrid=_VOLTAGE_MRID,
    name="Voltage (V)",
    accumulation=AccumulationKind.INSTANTANEOUS,
    flow_direction=FlowDirectionKind.NONE,
    commodity=CommodityKind.ELECTRICITY_SECONDARY_METERED,
    measurement_kind=MeasurementKind.VOLTAGE,
    unit=UnitSymbol.V,
    phase=PhaseCode.NONE,
    measuring_period_minutes=15,
    multiplier=1.0,
)


class DataGenerator:
    """Generates realistic interval reading data for simulated meters.

    Load curve patterns:
        - Residential: duck curve with overnight trough, morning ramp,
          midday plateau, evening peak, decline
        - C&I: weekday high (07:00-18:00), weekend at 30% of weekday

    Quality injection rates:
        - 2% ESTIMATED, 0.5% SUSPECT, 0.2% MISSING
        - COMM_FAILURE meters: 10-20% MISSING

    References:
        - Typical utility load profile curves
        - IEC 61968-9:2024, reading quality codes
        - ANSI C84.1 voltage ranges
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

    def get_reading_types(self) -> dict[str, ReadingType]:
        """Return the catalog of available reading types."""
        return dict(READING_TYPES)

    def get_reading_type_mrids_for_meter(self, meter: Meter, is_solar: bool) -> list[str]:
        """Determine which reading types apply to a given meter."""
        mrids = [_FORWARD_ENERGY_MRID, _DEMAND_MRID, _VOLTAGE_MRID]
        if is_solar:
            mrids.append(_REVERSE_ENERGY_MRID)
        return mrids

    def generate_meter_readings(
        self,
        meter: Meter,
        is_solar: bool,
        data_days: int,
        interval_minutes: int,
    ) -> list[MeterReading]:
        """Generate all reading types for a meter over the specified period.

        Args:
            meter: The meter to generate data for.
            is_solar: Whether this meter has reverse energy (solar).
            data_days: Number of days of historical data to generate.
            interval_minutes: Interval between readings in minutes.

        Returns:
            List of MeterReading objects, one per reading type.
        """
        if not self._enabled:
            return []
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        # Align to interval boundary
        minute_aligned = (now.minute // interval_minutes) * interval_minutes
        end_time = now.replace(minute=minute_aligned)
        start_time = end_time - timedelta(days=data_days)

        time_period = DateTimeInterval(start=start_time, end=end_time)
        rt_mrids = self.get_reading_type_mrids_for_meter(meter, is_solar)

        readings: list[MeterReading] = []
        for rt_mrid in rt_mrids:
            interval_block = self._generate_interval_block(
                meter, rt_mrid, is_solar, start_time, end_time, interval_minutes
            )
            meter_reading = MeterReading(
                mrid=generate_mrid(),
                meter_mrid=meter.mrid,
                usage_point_mrid=meter.usage_point_mrid,
                reading_type_mrid=rt_mrid,
                time_period=time_period,
                interval_blocks=[interval_block],
                is_validated=False,
            )
            readings.append(meter_reading)

        return readings

    def generate_on_demand_readings(
        self,
        meter: Meter,
        is_solar: bool,
        start: datetime,
        end: datetime,
        interval_minutes: int = 15,
        reading_type_mrid: str | None = None,
    ) -> list[MeterReading]:
        """Generate fresh readings for an on-demand meter read request.

        Unlike generate_meter_readings() which computes start/end from data_days,
        this method accepts explicit time boundaries — used when the HES collects
        a fresh reading from the meter through the communication network.

        Args:
            meter: The meter producing the reading.
            is_solar: Whether this meter has reverse energy (solar).
            start: Start of the requested time range.
            end: End of the requested time range.
            interval_minutes: Interval between readings in minutes.
            reading_type_mrid: If given, generate only this reading type;
                otherwise generate all applicable types.

        Returns:
            List of MeterReading objects (one per reading type).
        """
        if not self._enabled:
            return []

        time_period = DateTimeInterval(start=start, end=end)

        if reading_type_mrid:
            rt_mrids = [reading_type_mrid]
        else:
            rt_mrids = self.get_reading_type_mrids_for_meter(meter, is_solar)

        readings: list[MeterReading] = []
        for rt_mrid in rt_mrids:
            interval_block = self._generate_interval_block(
                meter, rt_mrid, is_solar, start, end, interval_minutes
            )
            meter_reading = MeterReading(
                mrid=generate_mrid(),
                meter_mrid=meter.mrid,
                usage_point_mrid=meter.usage_point_mrid,
                reading_type_mrid=rt_mrid,
                time_period=time_period,
                interval_blocks=[interval_block],
                is_validated=False,
            )
            readings.append(meter_reading)

        return readings

    def _generate_interval_block(
        self,
        meter: Meter,
        reading_type_mrid: str,
        is_solar: bool,
        start: datetime,
        end: datetime,
        interval_minutes: int,
    ) -> IntervalBlock:
        """Generate an interval block with realistic readings."""
        intervals: list[IntervalReading] = []
        current = start
        is_comm_failure = meter.status.value == "commFailure"

        while current < end:
            value = self._generate_value(meter, reading_type_mrid, is_solar, current)
            quality = self._generate_quality(is_comm_failure)
            # If MISSING, zero out the value
            if any(q.quality_type == ReadingQualityType.MISSING for q in quality):
                value = 0.0
            intervals.append(IntervalReading(
                timestamp=current,
                value=round(value, 2),
                quality=quality,
            ))
            current += timedelta(minutes=interval_minutes)

        return IntervalBlock(
            mrid=generate_mrid(),
            reading_type_mrid=reading_type_mrid,
            time_period=DateTimeInterval(start=start, end=end),
            interval_readings=intervals,
        )

    def _generate_value(
        self,
        meter: Meter,
        reading_type_mrid: str,
        is_solar: bool,
        timestamp: datetime,
    ) -> float:
        """Generate a realistic reading value based on meter type and time."""
        if reading_type_mrid == _VOLTAGE_MRID:
            return self._generate_voltage(meter, timestamp)
        elif reading_type_mrid == _REVERSE_ENERGY_MRID:
            return self._generate_reverse_energy(meter, timestamp)
        elif reading_type_mrid == _DEMAND_MRID:
            return self._generate_demand(meter, timestamp)
        else:  # Forward energy
            return self._generate_forward_energy(meter, timestamp)

    def _generate_forward_energy(self, meter: Meter, timestamp: datetime) -> float:
        """Generate forward active energy (Wh) for a 15-min interval.

        Residential: Duck curve pattern with seasonal variation.
        C&I: Weekday/weekend pattern with business hours peak.
        """
        is_residential = meter.meter_type in (MeterType.E350, MeterType.E360)

        if is_residential:
            return self._residential_energy(timestamp)
        else:
            return self._ci_energy(meter, timestamp)

    def _residential_energy(self, timestamp: datetime) -> float:
        """Residential load curve - duck curve pattern.

        Pattern (hourly):
            00:00-05:00 - overnight trough (0.3-0.8 kW)
            05:00-08:00 - morning ramp (0.8-2.5 kW)
            08:00-16:00 - midday plateau (1.0-2.0 kW)
            16:00-21:00 - evening peak (2.0-4.0 kW)
            21:00-24:00 - decline (1.0-0.5 kW)
        """
        hour = timestamp.hour + timestamp.minute / 60.0

        if hour < 5:
            base_kw = 0.3 + 0.5 * (hour / 5.0)
        elif hour < 8:
            base_kw = 0.8 + 1.7 * ((hour - 5) / 3.0)
        elif hour < 16:
            base_kw = 1.0 + 1.0 * math.sin(math.pi * (hour - 8) / 8)
        elif hour < 21:
            t = (hour - 16) / 5.0
            base_kw = 2.0 + 2.0 * math.sin(math.pi * t)
        else:
            base_kw = 1.0 - 0.5 * ((hour - 21) / 3.0)

        # Seasonal multiplier (summer peak via cosine, peak in July)
        # Ref: Typical utility seasonal load variation
        day_of_year = timestamp.timetuple().tm_yday
        seasonal = 1.0 + 0.3 * math.cos(2 * math.pi * (day_of_year - 182) / 365)

        # Add noise (15% Gaussian)
        noise = 1.0 + self._rng.gauss(0, 0.15)
        noise = max(0.1, noise)

        # Convert kW to Wh for 15-min interval: kW * 0.25h * 1000
        power_kw = base_kw * seasonal * noise
        energy_wh = power_kw * 0.25 * 1000
        return max(0.0, energy_wh)

    def _ci_energy(self, meter: Meter, timestamp: datetime) -> float:
        """C&I load profile - weekday/weekend pattern.

        Weekday: high demand 07:00-18:00
        Weekend: 30% of weekday
        Base range: 10-50 kW with 8% Gaussian noise.
        """
        hour = timestamp.hour + timestamp.minute / 60.0
        is_weekday = timestamp.weekday() < 5

        if is_weekday:
            if 7 <= hour < 18:
                base_kw = 30.0 + 20.0 * math.sin(math.pi * (hour - 7) / 11)
            else:
                base_kw = 10.0
        else:
            if 8 <= hour < 17:
                base_kw = 10.0 + 5.0 * math.sin(math.pi * (hour - 8) / 9)
            else:
                base_kw = 5.0

        noise = 1.0 + self._rng.gauss(0, 0.08)
        noise = max(0.1, noise)

        energy_wh = base_kw * noise * 0.25 * 1000
        return max(0.0, energy_wh)

    def _generate_demand(self, meter: Meter, timestamp: datetime) -> float:
        """Generate demand (W) - instantaneous power at interval end.

        Derived from energy: W = Wh / 0.25h
        """
        is_residential = meter.meter_type in (MeterType.E350, MeterType.E360)
        if is_residential:
            energy_wh = self._residential_energy(timestamp)
        else:
            energy_wh = self._ci_energy(meter, timestamp)
        return energy_wh / 0.25  # Convert Wh (15 min) back to W

    def _generate_voltage(self, meter: Meter, timestamp: datetime) -> float:
        """Generate voltage reading.

        Ref: ANSI C84.1 Range A for 120V nominal: 114V-126V (±5%)
        For 240V nominal (C&I): 228V-252V
        """
        is_residential = meter.meter_type in (MeterType.E350, MeterType.E360)
        nominal = 120.0 if is_residential else 240.0

        # Voltage varies slightly with load (drops during peak)
        hour = timestamp.hour + timestamp.minute / 60.0
        if 16 <= hour < 21:
            load_effect = -0.02  # slight voltage drop during peak
        elif 1 <= hour < 5:
            load_effect = 0.01  # slight rise during low load
        else:
            load_effect = 0.0

        noise = self._rng.gauss(0, 0.01)
        voltage = nominal * (1.0 + load_effect + noise)
        return voltage

    def _generate_reverse_energy(self, meter: Meter, timestamp: datetime) -> float:
        """Generate reverse energy for solar meters.

        Solar production peaks midday (10:00-15:00), zero at night.
        """
        hour = timestamp.hour + timestamp.minute / 60.0

        if 6 <= hour < 19:
            # Bell curve centered around 12:30
            solar_factor = math.exp(-0.5 * ((hour - 12.5) / 2.5) ** 2)
            base_kw = 3.0 * solar_factor  # Peak 3 kW solar generation
            noise = 1.0 + self._rng.gauss(0, 0.2)
            noise = max(0.0, noise)
            energy_wh = base_kw * noise * 0.25 * 1000
            return max(0.0, energy_wh)
        else:
            return 0.0

    def _generate_quality(self, is_comm_failure: bool) -> list[ReadingQuality]:
        """Generate quality annotations for a reading.

        Normal meters: 2% ESTIMATED, 0.5% SUSPECT, 0.2% MISSING
        COMM_FAILURE meters: 10-20% MISSING

        References:
            - IEC 61968-9:2024, Section 6.4 "Reading Quality"
        """
        roll = self._rng.random()

        if is_comm_failure:
            missing_rate = self._rng.uniform(0.10, 0.20)
            if roll < missing_rate:
                return [ReadingQuality(
                    quality_type=ReadingQualityType.MISSING,
                    comment="Communication failure - no data received",
                    source="HES",
                )]

        if roll < 0.002:
            return [ReadingQuality(
                quality_type=ReadingQualityType.MISSING,
                comment="Data gap detected",
                source="HES",
            )]
        elif roll < 0.007:
            return [ReadingQuality(
                quality_type=ReadingQualityType.SUSPECT,
                comment="Value outside expected range",
                source="HES",
            )]
        elif roll < 0.027:
            return [ReadingQuality(
                quality_type=ReadingQualityType.ESTIMATED,
                comment="Estimated from adjacent intervals",
                source="HES",
            )]

        return [ReadingQuality(
            quality_type=ReadingQualityType.VALID,
            source="HES",
        )]
