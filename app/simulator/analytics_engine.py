"""Simulated analytics platform for demand, voltage, and revenue protection.

References:
    - Landis+Gyr Gridstream Analytics Solution Overview (publicly available)
    - ANSI C84.1 - Electric Power Systems and Equipment Voltage Ratings
      Range A (normal): 114V-126V for 120V nominal (±5%)
      Range A (normal): 228V-252V for 240V nominal (±5%)
    - IEC 61968-9:2024, analytics concepts
"""

import math
from datetime import datetime

from app.models.analytics import (
    DemandDataPoint,
    DemandSummary,
    RevenueProtectionAlert,
    VoltageDataPoint,
    VoltageSummary,
)
from app.models.common import DateTimeInterval, generate_mrid
from app.models.enums import MeterType, ReadingQualityType
from app.simulator.headend import Headend


class AnalyticsEngine:
    """Simulated analytics platform.

    References:
        - Landis+Gyr Gridstream Analytics capabilities
        - ANSI C84.1 voltage range compliance analysis
    """

    # ANSI C84.1 Range A thresholds
    # Ref: ANSI C84.1-2020, Table 1
    VOLTAGE_RANGE_A = {
        120.0: (114.0, 126.0),  # ±5% of 120V
        240.0: (228.0, 252.0),  # ±5% of 240V
    }

    def __init__(self, headend: Headend):
        self._headend = headend

    def get_demand_summary(
        self,
        start: datetime,
        end: datetime,
        meter_mrid: str | None = None,
    ) -> list[DemandSummary]:
        """Calculate demand statistics for one or all meters.

        Args:
            start: Start of analysis period.
            end: End of analysis period.
            meter_mrid: Optional specific meter (None for all).

        Returns:
            List of DemandSummary objects.
        """
        meters = self._headend.get_meters()
        if meter_mrid:
            meter = meters.get(meter_mrid)
            if not meter:
                return []
            meter_list = [(meter_mrid, meter)]
        else:
            meter_list = list(meters.items())

        summaries: list[DemandSummary] = []
        time_period = DateTimeInterval(start=start, end=end)

        for m_mrid, meter in meter_list:
            readings = self._headend.get_meter_readings(
                m_mrid, start, end, "rt-demand-w"
            )

            data_points: list[DemandDataPoint] = []
            for reading in readings:
                for block in reading.interval_blocks:
                    for ir in block.interval_readings:
                        if not any(
                            q.quality_type == ReadingQualityType.MISSING
                            for q in ir.quality
                        ):
                            data_points.append(DemandDataPoint(
                                timestamp=ir.timestamp,
                                demand_w=ir.value,
                            ))

            if not data_points:
                continue

            values = [dp.demand_w for dp in data_points]
            peak = max(values)
            peak_ts = data_points[values.index(peak)].timestamp
            avg = sum(values) / len(values)
            min_val = min(values)
            load_factor = avg / peak if peak > 0 else 0.0

            summaries.append(DemandSummary(
                meter_mrid=m_mrid,
                time_period=time_period,
                peak_demand_w=round(peak, 2),
                peak_demand_timestamp=peak_ts,
                average_demand_w=round(avg, 2),
                min_demand_w=round(min_val, 2),
                load_factor=round(load_factor, 4),
                data_points=data_points[:100],  # Limit for API response size
            ))

        return summaries

    def get_voltage_summary(
        self,
        start: datetime,
        end: datetime,
        meter_mrid: str | None = None,
    ) -> list[VoltageSummary]:
        """Calculate voltage statistics with ANSI C84.1 compliance.

        Args:
            start: Start of analysis period.
            end: End of analysis period.
            meter_mrid: Optional specific meter (None for all).

        Returns:
            List of VoltageSummary objects.

        References:
            - ANSI C84.1 Range A: ±5% of nominal voltage
        """
        meters = self._headend.get_meters()
        if meter_mrid:
            meter = meters.get(meter_mrid)
            if not meter:
                return []
            meter_list = [(meter_mrid, meter)]
        else:
            meter_list = list(meters.items())

        summaries: list[VoltageSummary] = []
        time_period = DateTimeInterval(start=start, end=end)

        for m_mrid, meter in meter_list:
            readings = self._headend.get_meter_readings(
                m_mrid, start, end, "rt-voltage-v"
            )

            data_points: list[VoltageDataPoint] = []
            for reading in readings:
                for block in reading.interval_blocks:
                    for ir in block.interval_readings:
                        if not any(
                            q.quality_type == ReadingQualityType.MISSING
                            for q in ir.quality
                        ):
                            data_points.append(VoltageDataPoint(
                                timestamp=ir.timestamp,
                                voltage_v=ir.value,
                            ))

            if not data_points:
                continue

            values = [dp.voltage_v for dp in data_points]
            avg = sum(values) / len(values)
            max_v = max(values)
            min_v = min(values)

            # Standard deviation
            variance = sum((v - avg) ** 2 for v in values) / len(values)
            std_dev = math.sqrt(variance)

            # ANSI C84.1 Range A exceedance
            is_residential = meter.meter_type in (MeterType.E350, MeterType.E360)
            nominal = 120.0 if is_residential else 240.0
            low, high = self.VOLTAGE_RANGE_A.get(nominal, (nominal * 0.95, nominal * 1.05))
            exceedance = sum(1 for v in values if v < low or v > high)

            summaries.append(VoltageSummary(
                meter_mrid=m_mrid,
                time_period=time_period,
                average_voltage_v=round(avg, 2),
                max_voltage_v=round(max_v, 2),
                min_voltage_v=round(min_v, 2),
                std_dev_voltage_v=round(std_dev, 4),
                ansi_c84_1_exceedance_count=exceedance,
                data_points=data_points[:100],  # Limit for API response size
            ))

        return summaries

    def get_revenue_protection_alerts(
        self,
        start: datetime,
        end: datetime,
    ) -> list[RevenueProtectionAlert]:
        """Generate revenue protection alerts based on anomaly detection.

        Alert types:
            - reverse_flow: Unexpected reverse energy on non-solar meters
            - consumption_anomaly: Sudden drop (>80%) in consumption
            - tamper: Simulated tamper detection events

        References:
            - Landis+Gyr Gridstream Analytics revenue protection capabilities
        """
        alerts: list[RevenueProtectionAlert] = []
        meters = self._headend.get_meters()
        time_period = DateTimeInterval(start=start, end=end)

        for m_mrid, meter in meters.items():
            # Check for reverse flow on non-solar meters
            is_solar = self._headend.meter_park.is_solar_meter(meter)
            if not is_solar:
                reverse_readings = self._headend.get_meter_readings(
                    m_mrid, start, end, "rt-reverse-energy-wh"
                )
                if reverse_readings:
                    for reading in reverse_readings:
                        for block in reading.interval_blocks:
                            has_reverse = any(
                                ir.value > 0 for ir in block.interval_readings
                            )
                            if has_reverse:
                                alerts.append(RevenueProtectionAlert(
                                    mrid=generate_mrid(),
                                    meter_mrid=m_mrid,
                                    alert_type="reverse_flow",
                                    severity="high",
                                    detected_at=datetime.now(tz=start.tzinfo),
                                    description=(
                                        f"Reverse energy flow detected on non-solar meter "
                                        f"{meter.serial_number}"
                                    ),
                                    time_period=time_period,
                                ))

            # Check for consumption anomaly (very low readings for active meters)
            energy_readings = self._headend.get_meter_readings(
                m_mrid, start, end, "rt-forward-energy-wh"
            )
            if energy_readings:
                for reading in energy_readings:
                    for block in reading.interval_blocks:
                        valid_values = [
                            ir.value for ir in block.interval_readings
                            if ir.value > 0 and all(
                                q.quality_type == ReadingQualityType.VALID
                                for q in ir.quality
                            )
                        ]
                        if len(valid_values) > 10:
                            avg = sum(valid_values) / len(valid_values)
                            # Count intervals with < 20% of average
                            anomalous = sum(
                                1 for v in valid_values if v < avg * 0.2
                            )
                            if anomalous > len(valid_values) * 0.1:
                                alerts.append(RevenueProtectionAlert(
                                    mrid=generate_mrid(),
                                    meter_mrid=m_mrid,
                                    alert_type="consumption_anomaly",
                                    severity="medium",
                                    detected_at=datetime.now(tz=start.tzinfo),
                                    description=(
                                        f"Consumption anomaly detected on meter "
                                        f"{meter.serial_number}: "
                                        f"{anomalous} intervals below 20% of average"
                                    ),
                                    time_period=time_period,
                                ))

        return alerts
