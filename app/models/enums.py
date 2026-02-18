"""CIM enumerations for metering domain.

References:
    - IEC 61968-9:2024, Section 6 "Information Model"
    - TC57CIM Python reference: https://github.com/pjm4github/TC57CIM
    - CIMug standards artifacts: https://cimug.org/cimdocs/standards-artifacts/
"""

from enum import Enum


class FlowDirectionKind(str, Enum):
    """Direction of energy flow for a reading type.

    References:
        - IEC 61968-9:2024, ReadingType coded attributes
        - TC57CIM: IEC61968/Metering/FlowDirectionKind.py
          (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/FlowDirectionKind.py)
    """

    FORWARD = "forward"
    REVERSE = "reverse"
    NET = "net"
    TOTAL = "total"
    NONE = "none"


class CommodityKind(str, Enum):
    """Kind of commodity being measured.

    References:
        - IEC 61968-9:2024, ReadingType coded attributes
        - TC57CIM: IEC61968/Metering/CommodityKind.py
          (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/CommodityKind.py)
    """

    ELECTRICITY_PRIMARY_METERED = "electricityPrimaryMetered"
    ELECTRICITY_SECONDARY_METERED = "electricitySecondaryMetered"
    NONE = "none"


class MeasurementKind(str, Enum):
    """Kind of measurement for a reading type.

    References:
        - IEC 61968-9:2024, ReadingType coded attributes
        - TC57CIM: IEC61968/Metering/MeasurementKind.py
          (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/MeasurementKind.py)
    """

    ENERGY = "energy"
    DEMAND = "demand"
    VOLTAGE = "voltage"
    CURRENT = "current"
    POWER = "power"
    POWER_FACTOR = "powerFactor"
    FREQUENCY = "frequency"
    NONE = "none"


class AccumulationKind(str, Enum):
    """Kind of accumulation behaviour for a reading type.

    References:
        - IEC 61968-9:2024, ReadingType coded attributes
        - TC57CIM: IEC61968/Metering/AccumulationKind.py
          (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/AccumulationKind.py)
    """

    NONE = "none"
    BULK_QUANTITY = "bulkQuantity"
    DELTA_DATA = "deltaData"
    INDICATING = "indicating"
    SUMMATION = "summation"
    INSTANTANEOUS = "instantaneous"


class UnitSymbol(str, Enum):
    """Unit symbols used in CIM measurements.

    References:
        - IEC 61970-301, UnitSymbol enumeration
        - TC57CIM: IEC61970/Base/Domain/UnitSymbol
          (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61970/Base/Domain/UnitSymbol.py)
    """

    WH = "Wh"
    W = "W"
    V = "V"
    A = "A"
    VA = "VA"
    VAR = "VAr"
    HZ = "Hz"
    NONE = "none"


class PhaseCode(str, Enum):
    """Enumeration of phase identifiers.

    References:
        - IEC 61970-301, PhaseCode enumeration
        - TC57CIM: IEC61970/Base/Core/PhaseCode
          (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61970/Base/Core/PhaseCode.py)
    """

    A = "A"
    B = "B"
    C = "C"
    AB = "AB"
    BC = "BC"
    AC = "AC"
    ABC = "ABC"
    AN = "AN"
    BN = "BN"
    CN = "CN"
    ABN = "ABN"
    BCN = "BCN"
    ACN = "ACN"
    ABCN = "ABCN"
    NONE = "none"


class ReadingQualityType(str, Enum):
    """Quality classification for interval readings.

    References:
        - IEC 61968-9:2024, Section 6.4 "Reading Quality"
        - TC57CIM: IEC61968/Metering/ReadingQualityType.py
          (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/ReadingQualityType.py)
    """

    VALID = "valid"
    ESTIMATED = "estimated"
    SUSPECT = "suspect"
    MISSING = "missing"
    MANUALLY_EDITED = "manuallyEdited"


class ConnectionState(str, Enum):
    """Usage point connection state.

    References:
        - IEC 61968-9:2024, UsagePointConnectedKind
        - TC57CIM: IEC61968/Metering/UsagePointConnectedKind.py
          (https://github.com/pjm4github/TC57CIM/blob/master/py/IEC61968/Metering/UsagePointConnectedKind.py)
    """

    CONNECTED = "connected"
    PHYSICALLY_DISCONNECTED = "physicallyDisconnected"
    LOGICALLY_DISCONNECTED = "logicallyDisconnected"


class MeterType(str, Enum):
    """Landis+Gyr meter model types.

    References:
        - Landis+Gyr E350 Brochure (publicly available)
        - Landis+Gyr E360 LTE Technical Data (publicly available)
        - Landis+Gyr E650 S4x Product Specifications (publicly available)
        - Landis+Gyr E660/Revelo IoT Grid Sensing Platform (publicly available)
    """

    E350 = "E350"
    E360 = "E360"
    S4X_E650 = "S4x/E650"
    E660_REVELO = "E660/Revelo"


class CommunicationType(str, Enum):
    """Communication technology types for AMI networks.

    References:
        - Landis+Gyr AMI Communication Pathway Selection Guide (publicly available)
        - Gridstream platform communication specifications
    """

    RF_MESH = "RF Mesh"
    PLC = "PLC"
    CELLULAR_LTE = "Cellular LTE"


class MeterStatus(str, Enum):
    """Operational status of a meter.

    References:
        - Landis+Gyr Gridstream HES meter lifecycle states
    """

    ACTIVE = "active"
    COMM_FAILURE = "commFailure"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class DeliveryPromiseStatus(str, Enum):
    """Status of an asynchronous delivery promise for on-demand meter reads.

    References:
        - IEC 61968-9:2024, Section 9 "Message Exchanges" (async request patterns)
        - Landis+Gyr Gridstream HES on-demand read workflow
    """

    PENDING = "pending"
    IN_PROGRESS = "inProgress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class MeterDeliveryStatus(str, Enum):
    """Per-meter collection status within a delivery promise.

    References:
        - Landis+Gyr Gridstream HES per-device read status codes
    """

    PENDING = "pending"
    COLLECTED = "collected"
    FAILED = "failed"
