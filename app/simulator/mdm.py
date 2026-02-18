"""Simulated Meter Data Management (MDM) system with VEE pipeline.

The MDM receives raw readings from the HES and applies Validation, Estimation,
and Editing (VEE) processing to produce billing-quality data.

VEE Pipeline:
    1. Validation: Range checks, spike detection
    2. Estimation: Linear interpolation for MISSING gaps
    3. Editing: Quality flag management, is_validated=True

References:
    - Landis+Gyr Core MDMS Product Documentation (publicly available)
    - IEC 61968-9:2024, Section 7 "VEE Processing"
    - ANSI C12.20 metering accuracy standards
"""

from datetime import datetime

from app.models.common import DateTimeInterval
from app.models.enums import ReadingQualityType
from app.models.reading import IntervalReading, MeterReading, ReadingQuality
from app.simulator.headend import Headend


class MDM:
    """Simulated Meter Data Management system with VEE processing.

    References:
        - Landis+Gyr Core MDMS Product Documentation
        - IEC 61968-9:2024, VEE processing concepts
    """

    # Validation thresholds
    # Ref: Typical VEE range check parameters
    ENERGY_MAX_WH = 500_000.0  # Max 15-min energy (500 kWh, generous for C&I)
    ENERGY_MIN_WH = 0.0
    VOLTAGE_MAX_V = 280.0
    VOLTAGE_MIN_V = 100.0
    SPIKE_MULTIPLIER = 5.0  # Flag if value > 5x rolling average

    def __init__(self, headend: Headend):
        self._headend = headend
        self._enabled: bool = True

    def start(self) -> None:
        self._enabled = True

    def stop(self) -> None:
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def get_validated_readings(
        self,
        meter_mrid: str,
        start: datetime | None = None,
        end: datetime | None = None,
        reading_type_mrid: str | None = None,
    ) -> list[MeterReading]:
        """Get VEE-processed readings for a meter.

        Applies the full VEE pipeline: validation, estimation, editing.

        Args:
            meter_mrid: Meter to query.
            start: Optional start of time range.
            end: Optional end of time range.
            reading_type_mrid: Optional reading type filter.

        Returns:
            List of validated MeterReading objects.
        """
        if not self._enabled:
            return []
        raw_readings = self._headend.get_meter_readings(
            meter_mrid, start, end, reading_type_mrid
        )
        return [self._apply_vee(r) for r in raw_readings]

    def _apply_vee(self, reading: MeterReading) -> MeterReading:
        """Apply the VEE pipeline to a meter reading.

        Pipeline:
            1. Validate: range checks and spike detection
            2. Estimate: fill MISSING gaps via linear interpolation
            3. Edit: update quality flags, mark as validated
        """
        new_blocks = []
        for block in reading.interval_blocks:
            intervals = list(block.interval_readings)

            # Step 1: Validation
            intervals = self._validate(intervals, reading.reading_type_mrid)

            # Step 2: Estimation
            intervals = self._estimate(intervals)

            # Step 3: Editing
            intervals = self._edit(intervals)

            new_block = block.model_copy(update={"interval_readings": intervals})
            new_blocks.append(new_block)

        return reading.model_copy(update={
            "interval_blocks": new_blocks,
            "is_validated": True,
        })

    def _validate(
        self, intervals: list[IntervalReading], reading_type_mrid: str
    ) -> list[IntervalReading]:
        """Validation step: range checks and spike detection.

        References:
            - IEC 61968-9:2024, VEE validation rules
            - ANSI C12.20 metering accuracy standards
        """
        validated = []
        values = [ir.value for ir in intervals if ir.value > 0]
        avg_value = sum(values) / len(values) if values else 1.0

        is_voltage = "voltage" in reading_type_mrid

        for ir in intervals:
            new_quality = list(ir.quality)
            is_already_flagged = any(
                q.quality_type in (ReadingQualityType.MISSING, ReadingQualityType.SUSPECT)
                for q in new_quality
            )

            if not is_already_flagged:
                # Range check
                if is_voltage:
                    if ir.value < self.VOLTAGE_MIN_V or ir.value > self.VOLTAGE_MAX_V:
                        new_quality = [ReadingQuality(
                            quality_type=ReadingQualityType.SUSPECT,
                            comment=f"Voltage out of range: {ir.value:.1f}V",
                            source="MDM-VEE",
                        )]
                else:
                    if ir.value < self.ENERGY_MIN_WH or ir.value > self.ENERGY_MAX_WH:
                        new_quality = [ReadingQuality(
                            quality_type=ReadingQualityType.SUSPECT,
                            comment=f"Value out of range: {ir.value:.2f}",
                            source="MDM-VEE",
                        )]

                # Spike detection
                if ir.value > avg_value * self.SPIKE_MULTIPLIER and ir.value > 0:
                    new_quality = [ReadingQuality(
                        quality_type=ReadingQualityType.SUSPECT,
                        comment=f"Spike detected: {ir.value:.2f} vs avg {avg_value:.2f}",
                        source="MDM-VEE",
                    )]

            validated.append(ir.model_copy(update={"quality": new_quality}))

        return validated

    def _estimate(self, intervals: list[IntervalReading]) -> list[IntervalReading]:
        """Estimation step: linear interpolation for MISSING gaps.

        References:
            - IEC 61968-9:2024, estimation methods
            - Linear interpolation as standard gap-fill technique
        """
        estimated = list(intervals)

        for i, ir in enumerate(estimated):
            is_missing = any(
                q.quality_type == ReadingQualityType.MISSING for q in ir.quality
            )
            if is_missing:
                # Find nearest valid neighbors for interpolation
                prev_val = self._find_prev_valid(estimated, i)
                next_val = self._find_next_valid(estimated, i)

                if prev_val is not None and next_val is not None:
                    interpolated = (prev_val + next_val) / 2.0
                elif prev_val is not None:
                    interpolated = prev_val
                elif next_val is not None:
                    interpolated = next_val
                else:
                    interpolated = 0.0

                estimated[i] = ir.model_copy(update={
                    "value": round(interpolated, 2),
                    "quality": [ReadingQuality(
                        quality_type=ReadingQualityType.ESTIMATED,
                        comment="Linear interpolation for missing data",
                        source="MDM-VEE",
                    )],
                })

        return estimated

    def _find_prev_valid(
        self, intervals: list[IntervalReading], index: int
    ) -> float | None:
        """Find the nearest previous valid reading value."""
        for i in range(index - 1, -1, -1):
            if all(
                q.quality_type == ReadingQualityType.VALID
                for q in intervals[i].quality
            ):
                return intervals[i].value
        return None

    def _find_next_valid(
        self, intervals: list[IntervalReading], index: int
    ) -> float | None:
        """Find the nearest next valid reading value."""
        for i in range(index + 1, len(intervals)):
            if all(
                q.quality_type == ReadingQualityType.VALID
                for q in intervals[i].quality
            ):
                return intervals[i].value
        return None

    def _edit(self, intervals: list[IntervalReading]) -> list[IntervalReading]:
        """Editing step: finalize quality flags.

        Mark remaining SUSPECT readings as MANUALLY_EDITED with note.
        """
        edited = []
        for ir in intervals:
            # Leave quality as-is for the simulation
            # In a real MDM, suspects would go to an exception queue
            edited.append(ir)
        return edited

    def get_billing_determinants(
        self, meter_mrid: str, start: datetime, end: datetime
    ) -> dict:
        """Calculate billing determinants from validated readings.

        Returns total kWh, peak kW, and simplified on/off-peak split.

        References:
            - Typical utility billing determinant calculations
            - IEC 61968-9:2024, billing data concepts
        """
        readings = self.get_validated_readings(meter_mrid, start, end, "rt-forward-energy-wh")

        total_wh = 0.0
        peak_w = 0.0
        on_peak_wh = 0.0
        off_peak_wh = 0.0

        for reading in readings:
            for block in reading.interval_blocks:
                for ir in block.interval_readings:
                    total_wh += ir.value
                    demand_w = ir.value / 0.25  # Convert 15-min Wh to W
                    peak_w = max(peak_w, demand_w)

                    # Simple on-peak: weekdays 12:00-20:00
                    if ir.timestamp.weekday() < 5 and 12 <= ir.timestamp.hour < 20:
                        on_peak_wh += ir.value
                    else:
                        off_peak_wh += ir.value

        return {
            "total_kwh": round(total_wh / 1000.0, 2),
            "peak_kw": round(peak_w / 1000.0, 2),
            "on_peak_kwh": round(on_peak_wh / 1000.0, 2),
            "off_peak_kwh": round(off_peak_wh / 1000.0, 2),
            "period": DateTimeInterval(start=start, end=end).model_dump(mode="json"),
        }
