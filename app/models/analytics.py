"""Analytics models for demand, voltage, and revenue protection.

References:
    - Landis+Gyr Gridstream Analytics Solution Overview (publicly available)
    - ANSI C84.1 - Electric Power Systems and Equipment Voltage Ratings
    - IEC 61968-9:2024, demand and voltage measurement concepts
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.common import DateTimeInterval


class DemandDataPoint(BaseModel):
    """A single demand measurement data point."""

    timestamp: datetime = Field(description="Measurement timestamp (UTC)")
    demand_w: float = Field(description="Demand value in watts")


class DemandSummary(BaseModel):
    """Aggregated demand statistics for a meter or fleet.

    References:
        - Landis+Gyr Gridstream Analytics demand analysis capabilities
        - IEC 61968-9:2024, demand interval measurement
    """

    meter_mrid: str | None = Field(default=None, description="Meter mRID (None for fleet summary)")
    time_period: DateTimeInterval = Field(description="Analysis period")
    peak_demand_w: float = Field(description="Maximum demand in watts")
    peak_demand_timestamp: datetime = Field(description="Timestamp of peak demand")
    average_demand_w: float = Field(description="Average demand in watts")
    min_demand_w: float = Field(description="Minimum demand in watts")
    load_factor: float = Field(description="Load factor (average / peak), range 0.0-1.0")
    data_points: list[DemandDataPoint] = Field(
        default_factory=list, description="Individual demand data points"
    )


class VoltageDataPoint(BaseModel):
    """A single voltage measurement data point."""

    timestamp: datetime = Field(description="Measurement timestamp (UTC)")
    voltage_v: float = Field(description="Voltage value in volts")


class VoltageSummary(BaseModel):
    """Voltage statistics with ANSI C84.1 Range A compliance analysis.

    References:
        - ANSI C84.1 - Electric Power Systems and Equipment Voltage Ratings
          Range A (normal): 114V-126V for 120V nominal (±5%)
        - Landis+Gyr Gridstream Analytics voltage analysis capabilities
    """

    meter_mrid: str | None = Field(default=None, description="Meter mRID (None for fleet summary)")
    time_period: DateTimeInterval = Field(description="Analysis period")
    average_voltage_v: float = Field(description="Average voltage in volts")
    max_voltage_v: float = Field(description="Maximum voltage in volts")
    min_voltage_v: float = Field(description="Minimum voltage in volts")
    std_dev_voltage_v: float = Field(description="Standard deviation of voltage")
    ansi_c84_1_exceedance_count: int = Field(
        description="Number of intervals outside ANSI C84.1 Range A (±5% of nominal)"
    )
    data_points: list[VoltageDataPoint] = Field(
        default_factory=list, description="Individual voltage data points"
    )


class RevenueProtectionAlert(BaseModel):
    """Revenue protection anomaly alert.

    References:
        - Landis+Gyr Gridstream Analytics revenue protection capabilities
        - Common tamper detection patterns in AMI systems
    """

    mrid: str = Field(description="Alert identifier")
    meter_mrid: str = Field(description="Affected meter mRID")
    alert_type: str = Field(description="Alert type (tamper, bypass, reverse_flow, consumption_anomaly)")
    severity: str = Field(description="Alert severity (low, medium, high, critical)")
    detected_at: datetime = Field(description="Detection timestamp (UTC)")
    description: str = Field(description="Human-readable alert description")
    time_period: DateTimeInterval = Field(description="Period of anomalous behavior")
