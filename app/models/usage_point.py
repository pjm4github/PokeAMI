"""CIM UsagePoint model.

References:
    - IEC 61968-9:2024, Section 6.5 "Usage Point"
    - TC57CIM: IEC61968/Metering/UsagePoint.py
      (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/UsagePoint.py)
    - CIM UML: Available from cimug.org standards artifacts
      (https://cimug.org/cimdocs/standards-artifacts/)
"""

from pydantic import BaseModel, Field

from app.models.enums import ConnectionState, PhaseCode


class UsagePoint(BaseModel):
    """CIM UsagePoint - A logical or physical point in the network where consumption is measured.

    References:
        - IEC 61968-9:2024, UsagePoint
        - TC57CIM: IEC61968/Metering/UsagePoint.py
        - CIM Primer Seventh Edition (EPRI 3002021840)
    """

    mrid: str = Field(description="CIM master resource identifier (UUID)")
    name: str = Field(description="Human-readable name for this usage point")
    connection_state: ConnectionState = Field(description="Electrical connection state")
    phase_code: PhaseCode = Field(description="Phase wiring configuration")
    rated_power_w: float = Field(description="Rated power capacity in watts")
    rated_voltage_v: float = Field(description="Rated voltage in volts")
    service_category: str = Field(description="Service category (e.g., residential, commercial)")
    meter_mrids: list[str] = Field(default_factory=list, description="Associated meter mRIDs")
    service_location_address: str = Field(description="Physical service address")
    customer_account_id: str = Field(description="Customer account identifier")
