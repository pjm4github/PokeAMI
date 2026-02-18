"""CIM data models for the Meter API.

References:
    - IEC 61968-9:2024 Ed 3.0 - Meter Reading and Control
    - TC57CIM Python reference: https://github.com/pjm4github/TC57CIM
    - CIMug standards artifacts: https://cimug.org/cimdocs/standards-artifacts/
"""

from app.models.enums import (
    AccumulationKind,
    CommodityKind,
    CommunicationType,
    ConnectionState,
    DeliveryPromiseStatus,
    FlowDirectionKind,
    MeasurementKind,
    MeterDeliveryStatus,
    MeterStatus,
    MeterType,
    PhaseCode,
    ReadingQualityType,
    UnitSymbol,
)
from app.models.common import DateTimeInterval, PaginatedResponse, generate_mrid
from app.models.meter import CommModule, EndDevice, Meter
from app.models.reading import (
    IntervalBlock,
    IntervalReading,
    MeterReading,
    ReadingQuality,
    ReadingType,
)
from app.models.usage_point import UsagePoint
from app.models.analytics import (
    DemandDataPoint,
    DemandSummary,
    RevenueProtectionAlert,
    VoltageDataPoint,
    VoltageSummary,
)
from app.models.delivery_promise import (
    DeliveryPromise,
    DeliveryPromiseRequest,
    MeterDeliveryResult,
)

__all__ = [
    # Enums
    "AccumulationKind",
    "CommodityKind",
    "CommunicationType",
    "ConnectionState",
    "FlowDirectionKind",
    "MeasurementKind",
    "MeterStatus",
    "MeterType",
    "PhaseCode",
    "ReadingQualityType",
    "UnitSymbol",
    # Common
    "DateTimeInterval",
    "PaginatedResponse",
    "generate_mrid",
    # Meter
    "CommModule",
    "EndDevice",
    "Meter",
    # Reading
    "IntervalBlock",
    "IntervalReading",
    "MeterReading",
    "ReadingQuality",
    "ReadingType",
    # UsagePoint
    "UsagePoint",
    # Analytics
    "DemandDataPoint",
    "DemandSummary",
    "RevenueProtectionAlert",
    "VoltageDataPoint",
    "VoltageSummary",
    # Delivery Promise
    "DeliveryPromise",
    "DeliveryPromiseRequest",
    "DeliveryPromiseStatus",
    "MeterDeliveryResult",
    "MeterDeliveryStatus",
]
