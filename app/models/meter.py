"""CIM EndDevice and Meter models.

References:
    - IEC 61968-9:2024, Section 6.2 "End Device Model"
    - TC57CIM: IEC61968/Metering/EndDevice.py
      (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/EndDevice.py)
    - TC57CIM: IEC61968/Metering/Meter.py
      (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/Meter.py)
    - TC57CIM: IEC61968/Metering/ComModule.py
      (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/ComModule.py)
    - CIM UML: Available from cimug.org standards artifacts
      (https://cimug.org/cimdocs/standards-artifacts/)
    - Landis+Gyr E350 Datasheet (publicly available)
    - Landis+Gyr E360 LTE Technical Data (publicly available)
    - Landis+Gyr E650 S4x Product Specifications (publicly available)
    - Landis+Gyr E660/Revelo IoT Grid Sensing Platform (publicly available)
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    CommunicationType,
    ConnectionState,
    MeterStatus,
    MeterType,
    PhaseCode,
)


class CommModule(BaseModel):
    """Communication module attached to an end device.

    References:
        - TC57CIM: IEC61968/Metering/ComModule.py
        - Landis+Gyr AMI Communication Pathway Selection Guide (publicly available)
        - Gridstream platform communication specifications
    """

    comm_type: CommunicationType = Field(description="Communication technology")
    firmware_version: str = Field(description="Communication module firmware version")
    mac_address: str = Field(description="MAC address of the communication module")
    signal_strength: float = Field(description="Signal strength in dBm")
    last_communication: datetime = Field(description="Last successful communication timestamp")


class EndDevice(BaseModel):
    """CIM EndDevice - An asset container performing one or more end device functions.

    References:
        - IEC 61968-9:2024, Section 6.2 "End Device Model"
        - TC57CIM: IEC61968/Metering/EndDevice.py
        - CIM UML: Available from cimug.org standards artifacts
    """

    mrid: str = Field(description="CIM master resource identifier (UUID)")
    serial_number: str = Field(description="Manufacturer's serial number")
    manufacturer: str = Field(default="Landis+Gyr", description="Device manufacturer")
    model: str = Field(description="Device model designation")
    firmware_version: str = Field(description="Device firmware version")
    status: MeterStatus = Field(description="Current operational status")
    connection_state: ConnectionState = Field(description="Electrical connection state")
    install_date: datetime = Field(description="Date the device was installed")
    phase_code: PhaseCode = Field(description="Phase wiring configuration")
    comm_module: CommModule = Field(description="Attached communication module")
    usage_point_mrid: str = Field(description="Associated usage point mRID")


class Meter(EndDevice):
    """CIM Meter - A physical device that performs the metering role of the end device.

    Extends EndDevice with meter-specific attributes.

    References:
        - IEC 61968-9:2024, Section 6.2 "End Device Model"
        - TC57CIM: IEC61968/Metering/Meter.py
        - Landis+Gyr meter product specifications
    """

    meter_type: MeterType = Field(description="Landis+Gyr meter model type")
    rated_power_w: float = Field(description="Rated power capacity in watts")
    ct_ratio: float = Field(default=1.0, description="Current transformer ratio (1.0 = direct)")
    form_number: str = Field(description="ANSI meter form number")
    demand_interval_minutes: int = Field(default=15, description="Demand interval in minutes")
