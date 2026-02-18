"""CIM model validation tests.

Tests Pydantic validation, enum enforcement, and JSON serialization roundtrips.
"""

import json
from datetime import datetime, timezone

from app.models.common import DateTimeInterval, PaginatedResponse, generate_mrid
from app.models.enums import (
    AccumulationKind,
    CommodityKind,
    CommunicationType,
    ConnectionState,
    FlowDirectionKind,
    MeasurementKind,
    MeterStatus,
    MeterType,
    PhaseCode,
    ReadingQualityType,
    UnitSymbol,
)
from app.models.meter import CommModule, Meter
from app.models.reading import (
    IntervalBlock,
    IntervalReading,
    MeterReading,
    ReadingQuality,
    ReadingType,
)
from app.models.usage_point import UsagePoint
from app.models.analytics import DemandDataPoint, DemandSummary


class TestMRIDGeneration:
    def test_generate_mrid_is_uuid_string(self):
        mrid = generate_mrid()
        assert isinstance(mrid, str)
        assert len(mrid) == 36  # UUID format: 8-4-4-4-12

    def test_generate_mrid_unique(self):
        mrids = {generate_mrid() for _ in range(100)}
        assert len(mrids) == 100


class TestDateTimeInterval:
    def test_create_interval(self):
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 2, tzinfo=timezone.utc)
        interval = DateTimeInterval(start=start, end=end)
        assert interval.start == start
        assert interval.end == end

    def test_json_roundtrip(self):
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 2, tzinfo=timezone.utc)
        interval = DateTimeInterval(start=start, end=end)
        data = json.loads(interval.model_dump_json())
        restored = DateTimeInterval(**data)
        assert restored.start == start
        assert restored.end == end


class TestEnums:
    def test_flow_direction_values(self):
        assert FlowDirectionKind.FORWARD == "forward"
        assert FlowDirectionKind.REVERSE == "reverse"

    def test_meter_type_values(self):
        assert MeterType.E350 == "E350"
        assert MeterType.S4X_E650 == "S4x/E650"

    def test_meter_status_values(self):
        assert MeterStatus.ACTIVE == "active"
        assert MeterStatus.COMM_FAILURE == "commFailure"

    def test_reading_quality_type_values(self):
        assert ReadingQualityType.VALID == "valid"
        assert ReadingQualityType.ESTIMATED == "estimated"
        assert ReadingQualityType.MISSING == "missing"


class TestMeterModel:
    def test_create_meter(self):
        now = datetime.now(timezone.utc)
        meter = Meter(
            mrid=generate_mrid(),
            serial_number="E350-100000",
            manufacturer="Landis+Gyr",
            model="E350",
            firmware_version="7.3.1",
            status=MeterStatus.ACTIVE,
            connection_state=ConnectionState.CONNECTED,
            install_date=now,
            phase_code=PhaseCode.AN,
            comm_module=CommModule(
                comm_type=CommunicationType.RF_MESH,
                firmware_version="3.2.1",
                mac_address="aa:bb:cc:dd:ee:ff",
                signal_strength=-65.0,
                last_communication=now,
            ),
            usage_point_mrid=generate_mrid(),
            meter_type=MeterType.E350,
            rated_power_w=9600.0,
            form_number="2S",
        )
        assert meter.manufacturer == "Landis+Gyr"
        assert meter.meter_type == MeterType.E350

    def test_meter_json_roundtrip(self):
        now = datetime.now(timezone.utc)
        meter = Meter(
            mrid=generate_mrid(),
            serial_number="E350-100000",
            model="E350",
            firmware_version="7.3.1",
            status=MeterStatus.ACTIVE,
            connection_state=ConnectionState.CONNECTED,
            install_date=now,
            phase_code=PhaseCode.AN,
            comm_module=CommModule(
                comm_type=CommunicationType.RF_MESH,
                firmware_version="3.2.1",
                mac_address="aa:bb:cc:dd:ee:ff",
                signal_strength=-65.0,
                last_communication=now,
            ),
            usage_point_mrid=generate_mrid(),
            meter_type=MeterType.E350,
            rated_power_w=9600.0,
            form_number="2S",
        )
        data = json.loads(meter.model_dump_json())
        restored = Meter(**data)
        assert restored.serial_number == meter.serial_number


class TestReadingType:
    def test_create_reading_type(self):
        rt = ReadingType(
            mrid="rt-test",
            name="Test Reading",
            accumulation=AccumulationKind.DELTA_DATA,
            flow_direction=FlowDirectionKind.FORWARD,
            commodity=CommodityKind.ELECTRICITY_SECONDARY_METERED,
            measurement_kind=MeasurementKind.ENERGY,
            unit=UnitSymbol.WH,
        )
        assert rt.mrid == "rt-test"
        assert rt.multiplier == 1.0  # default


class TestIntervalReading:
    def test_create_with_quality(self):
        ir = IntervalReading(
            timestamp=datetime.now(timezone.utc),
            value=1234.56,
            quality=[
                ReadingQuality(quality_type=ReadingQualityType.VALID, source="HES")
            ],
        )
        assert ir.value == 1234.56
        assert len(ir.quality) == 1


class TestPaginatedResponse:
    def test_generic_pagination(self):
        resp = PaginatedResponse[str](
            total=100,
            limit=10,
            offset=0,
            items=["a", "b", "c"],
        )
        assert resp.total == 100
        assert len(resp.items) == 3
