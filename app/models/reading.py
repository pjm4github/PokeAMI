"""CIM Reading models - ReadingType, IntervalReading, IntervalBlock, MeterReading.

References:
    - IEC 61968-9:2024, Section 6.3 "Meter Reading Model"
    - IEC 61968-9:2024, Section 6.4 "Reading Quality"
    - TC57CIM: IEC61968/Metering/ReadingType.py
      (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/ReadingType.py)
    - TC57CIM: IEC61968/Metering/IntervalReading.py
      (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/IntervalReading.py)
    - TC57CIM: IEC61968/Metering/IntervalBlock.py
      (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/IntervalBlock.py)
    - TC57CIM: IEC61968/Metering/MeterReading.py
      (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/MeterReading.py)
    - CIM UML: Available from cimug.org standards artifacts
      (https://cimug.org/cimdocs/standards-artifacts/)
    - PNNL-34946: Power Application Developer's Guide to CIM (ReadingType 18-attribute structure)
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    AccumulationKind,
    CommodityKind,
    FlowDirectionKind,
    MeasurementKind,
    PhaseCode,
    ReadingQualityType,
    UnitSymbol,
)
from app.models.common import DateTimeInterval


class ReadingType(BaseModel):
    """CIM ReadingType - Detailed description of the type of reading values.

    CIM defines ReadingType with 18 coded attributes that together fully describe
    the nature of the reading. This model captures the most commonly used attributes.

    References:
        - IEC 61968-9:2024, ReadingType (18 coded attributes)
        - TC57CIM: IEC61968/Metering/ReadingType.py
        - PNNL-34946, Section 4.3 "ReadingType Structure"
        - CIM Primer Seventh Edition (EPRI 3002021840)
    """

    mrid: str = Field(description="Unique identifier for this reading type")
    name: str = Field(description="Human-readable name")
    accumulation: AccumulationKind = Field(description="How readings are accumulated")
    flow_direction: FlowDirectionKind = Field(description="Direction of energy flow")
    commodity: CommodityKind = Field(description="Commodity being measured")
    measurement_kind: MeasurementKind = Field(description="Kind of measurement")
    unit: UnitSymbol = Field(description="Unit of measure")
    phase: PhaseCode = Field(default=PhaseCode.NONE, description="Phase applicability")
    measuring_period_minutes: int = Field(default=15, description="Measurement interval in minutes")
    multiplier: float = Field(default=1.0, description="Value multiplier (e.g., kilo=1000)")


class ReadingQuality(BaseModel):
    """Quality annotation for a single interval reading.

    References:
        - IEC 61968-9:2024, Section 6.4 "Reading Quality"
        - TC57CIM: IEC61968/Metering/ReadingQualityType.py
    """

    quality_type: ReadingQualityType = Field(description="Quality classification")
    comment: str | None = Field(default=None, description="Optional quality comment")
    source: str = Field(default="HES", description="Source of the quality assessment")


class IntervalReading(BaseModel):
    """A single interval reading value with timestamp and quality.

    References:
        - IEC 61968-9:2024, IntervalReading
        - TC57CIM: IEC61968/Metering/IntervalReading.py
    """

    timestamp: datetime = Field(description="Start of the measurement interval (UTC)")
    value: float = Field(description="Measured value in the reading type's unit")
    quality: list[ReadingQuality] = Field(default_factory=list, description="Quality annotations")


class IntervalBlock(BaseModel):
    """A set of consecutive interval readings for a single reading type.

    References:
        - IEC 61968-9:2024, IntervalBlock
        - TC57CIM: IEC61968/Metering/IntervalBlock.py
    """

    mrid: str = Field(description="Unique identifier for this interval block")
    reading_type_mrid: str = Field(description="Associated reading type mRID")
    time_period: DateTimeInterval = Field(description="Time span covered by this block")
    interval_readings: list[IntervalReading] = Field(
        default_factory=list, description="Ordered interval readings"
    )


class MeterReading(BaseModel):
    """A set of interval blocks collected from a meter for a specific reading type.

    References:
        - IEC 61968-9:2024, MeterReading
        - TC57CIM: IEC61968/Metering/MeterReading.py
    """

    mrid: str = Field(description="Unique identifier for this meter reading")
    meter_mrid: str = Field(description="Source meter mRID")
    usage_point_mrid: str = Field(description="Associated usage point mRID")
    reading_type_mrid: str = Field(description="Reading type mRID")
    time_period: DateTimeInterval = Field(description="Time span for this meter reading")
    interval_blocks: list[IntervalBlock] = Field(
        default_factory=list, description="Contained interval blocks"
    )
    is_validated: bool = Field(default=False, description="Whether VEE processing is complete")
