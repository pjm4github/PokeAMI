# AMI OpenAPI — Agent Implementation Specification

This is a self-contained, machine-readable specification. An AI coding agent can read this document alone and produce a working REST API layer on top of any AMI backend that implements the interface contract in Section 10.

For the human-readable design rationale, architecture diagrams, and MCP alternative, see [OPENAPI_MCP_SPEC.md](./OPENAPI_MCP_SPEC.md).

---

## 1. Task Description

Implement a REST API layer on top of an existing AMI (Advanced Metering Infrastructure) backend. The backend already provides meter inventory, reading data, analytics, and communication network simulation. Your job is to create the HTTP interface only.

**Tech stack:** Python 3.13, FastAPI, Pydantic v2, pydantic-settings, uvicorn. All models use `BaseModel`. Configuration uses `BaseSettings` with `.env` support.

**Key constraint:** On-demand meter reads are asynchronous. The delivery promise pattern (Section 8) is the most complex and most important part of this API. Do not attempt to make on-demand reads synchronous.

**Standards basis:** IEC 61968-9:2024 (CIM for meter data exchange), ANSI C84.1 (voltage ranges).

---

## 2. Project Structure

```
app/
├── config.py              # Settings (pydantic-settings BaseSettings)
├── auth.py                # X-API-Key header validation dependency
├── main.py                # FastAPI app factory + lifespan + CORS
├── models/
│   ├── enums.py           # All enum definitions (str, Enum)
│   ├── common.py          # DateTimeInterval, PaginatedResponse[T], generate_mrid()
│   ├── meter.py           # CommModule, EndDevice, Meter
│   ├── reading.py         # ReadingQuality, IntervalReading, IntervalBlock, ReadingType, MeterReading
│   ├── usage_point.py     # UsagePoint
│   ├── analytics.py       # DemandDataPoint, DemandSummary, VoltageDataPoint, VoltageSummary, RevenueProtectionAlert
│   └── delivery_promise.py # DeliveryPromiseRequest, MeterDeliveryResult, DeliveryPromise
└── routers/
    ├── health.py          # GET /health (no auth)
    ├── meters.py          # GET /meters, GET /meters/{id}
    ├── readings.py        # GET /meters/{id}/readings, GET /interval-blocks
    ├── usage_points.py    # GET /usage-points, GET /usage-points/{id}, GET /usage-points/{id}/meter-readings
    ├── reading_types.py   # GET /reading-types
    ├── analytics.py       # GET /analytics/demand-summary, voltage-summary, revenue-protection-alerts
    └── delivery_promises.py # POST /delivery-promises, GET /delivery-promises/{id}, DELETE /delivery-promises/{id}, GET /delivery-promises
```

---

## 3. Configuration (`app/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str = "dev-api-key-change-me"
    meter_count: int = 50
    data_days: int = 30
    interval_minutes: int = 15
    host: str = "0.0.0.0"
    port: int = 8000
    dashboard_port: int = 8001
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

def get_settings() -> Settings:
    return Settings()
```

---

## 4. Authentication (`app/auth.py`)

All endpoints except `GET /health` require an `X-API-Key` header.

```python
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(
    api_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Missing API key. Provide X-API-Key header.")
    if api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid API key.")
    return api_key
```

---

## 5. Enumerations (`app/models/enums.py`)

All enums inherit from `(str, Enum)`. Exact string values matter — they appear in JSON responses and must match these definitions.

```python
from enum import Enum

class FlowDirectionKind(str, Enum):
    FORWARD = "forward"
    REVERSE = "reverse"
    NET = "net"
    TOTAL = "total"
    NONE = "none"

class CommodityKind(str, Enum):
    ELECTRICITY_PRIMARY_METERED = "electricityPrimaryMetered"
    ELECTRICITY_SECONDARY_METERED = "electricitySecondaryMetered"
    NONE = "none"

class MeasurementKind(str, Enum):
    ENERGY = "energy"
    DEMAND = "demand"
    VOLTAGE = "voltage"
    CURRENT = "current"
    POWER = "power"
    POWER_FACTOR = "powerFactor"
    FREQUENCY = "frequency"
    NONE = "none"

class AccumulationKind(str, Enum):
    NONE = "none"
    BULK_QUANTITY = "bulkQuantity"
    DELTA_DATA = "deltaData"
    INDICATING = "indicating"
    SUMMATION = "summation"
    INSTANTANEOUS = "instantaneous"

class UnitSymbol(str, Enum):
    WH = "Wh"
    W = "W"
    V = "V"
    A = "A"
    VA = "VA"
    VAR = "VAr"
    HZ = "Hz"
    NONE = "none"

class PhaseCode(str, Enum):
    A = "A"; B = "B"; C = "C"
    AB = "AB"; BC = "BC"; AC = "AC"; ABC = "ABC"
    AN = "AN"; BN = "BN"; CN = "CN"
    ABN = "ABN"; BCN = "BCN"; ACN = "ACN"; ABCN = "ABCN"
    NONE = "none"

class ReadingQualityType(str, Enum):
    VALID = "valid"
    ESTIMATED = "estimated"
    SUSPECT = "suspect"
    MISSING = "missing"
    MANUALLY_EDITED = "manuallyEdited"

class ConnectionState(str, Enum):
    CONNECTED = "connected"
    PHYSICALLY_DISCONNECTED = "physicallyDisconnected"
    LOGICALLY_DISCONNECTED = "logicallyDisconnected"

class MeterType(str, Enum):
    E350 = "E350"
    E360 = "E360"
    S4X_E650 = "S4x/E650"
    E660_REVELO = "E660/Revelo"

class CommunicationType(str, Enum):
    RF_MESH = "RF Mesh"
    PLC = "PLC"
    CELLULAR_LTE = "Cellular LTE"

class MeterStatus(str, Enum):
    ACTIVE = "active"
    COMM_FAILURE = "commFailure"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"

class DeliveryPromiseStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class MeterDeliveryStatus(str, Enum):
    PENDING = "pending"
    COLLECTED = "collected"
    FAILED = "failed"
```

---

## 6. Pydantic Models

### 6.1 `app/models/common.py`

```python
import uuid
from datetime import datetime
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

def generate_mrid() -> str:
    return str(uuid.uuid4())

class DateTimeInterval(BaseModel):
    start: datetime
    end: datetime

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    limit: int
    offset: int
    items: list[T]
```

### 6.2 `app/models/meter.py`

```python
from datetime import datetime
from pydantic import BaseModel
from app.models.enums import (CommunicationType, ConnectionState,
                               MeterStatus, MeterType, PhaseCode)

class CommModule(BaseModel):
    comm_type: CommunicationType
    firmware_version: str
    mac_address: str
    signal_strength: float      # dBm
    last_communication: datetime

class Meter(BaseModel):
    mrid: str
    serial_number: str
    manufacturer: str = "Landis+Gyr"
    model: str
    firmware_version: str
    status: MeterStatus
    connection_state: ConnectionState
    install_date: datetime
    phase_code: PhaseCode
    comm_module: CommModule
    usage_point_mrid: str
    meter_type: MeterType
    rated_power_w: float
    ct_ratio: float = 1.0
    form_number: str
    demand_interval_minutes: int = 15
```

### 6.3 `app/models/reading.py`

```python
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.common import DateTimeInterval
from app.models.enums import (AccumulationKind, CommodityKind, FlowDirectionKind,
                               MeasurementKind, PhaseCode, ReadingQualityType, UnitSymbol)

class ReadingQuality(BaseModel):
    quality_type: ReadingQualityType
    comment: str | None = None
    source: str = "HES"

class IntervalReading(BaseModel):
    timestamp: datetime
    value: float
    quality: list[ReadingQuality] = Field(default_factory=list)

class IntervalBlock(BaseModel):
    mrid: str
    reading_type_mrid: str
    time_period: DateTimeInterval
    interval_readings: list[IntervalReading] = Field(default_factory=list)

class ReadingType(BaseModel):
    mrid: str
    name: str
    accumulation: AccumulationKind
    flow_direction: FlowDirectionKind
    commodity: CommodityKind
    measurement_kind: MeasurementKind
    unit: UnitSymbol
    phase: PhaseCode = PhaseCode.NONE
    measuring_period_minutes: int = 15
    multiplier: float = 1.0

class MeterReading(BaseModel):
    mrid: str
    meter_mrid: str
    usage_point_mrid: str
    reading_type_mrid: str
    time_period: DateTimeInterval
    interval_blocks: list[IntervalBlock] = Field(default_factory=list)
    is_validated: bool = False
```

### 6.4 `app/models/usage_point.py`

```python
from pydantic import BaseModel, Field
from app.models.enums import ConnectionState, PhaseCode

class UsagePoint(BaseModel):
    mrid: str
    name: str
    connection_state: ConnectionState
    phase_code: PhaseCode
    rated_power_w: float
    rated_voltage_v: float
    service_category: str
    meter_mrids: list[str] = Field(default_factory=list)
    service_location_address: str
    customer_account_id: str
```

### 6.5 `app/models/analytics.py`

```python
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.common import DateTimeInterval

class DemandDataPoint(BaseModel):
    timestamp: datetime
    demand_w: float

class DemandSummary(BaseModel):
    meter_mrid: str | None = None
    time_period: DateTimeInterval
    peak_demand_w: float
    peak_demand_timestamp: datetime
    average_demand_w: float
    min_demand_w: float
    load_factor: float
    data_points: list[DemandDataPoint] = Field(default_factory=list)

class VoltageDataPoint(BaseModel):
    timestamp: datetime
    voltage_v: float

class VoltageSummary(BaseModel):
    meter_mrid: str | None = None
    time_period: DateTimeInterval
    average_voltage_v: float
    max_voltage_v: float
    min_voltage_v: float
    std_dev_voltage_v: float
    ansi_c84_1_exceedance_count: int
    data_points: list[VoltageDataPoint] = Field(default_factory=list)

class RevenueProtectionAlert(BaseModel):
    mrid: str
    meter_mrid: str
    alert_type: str       # tamper | bypass | reverse_flow | consumption_anomaly
    severity: str         # low | medium | high | critical
    detected_at: datetime
    description: str
    time_period: DateTimeInterval
```

### 6.6 `app/models/delivery_promise.py`

```python
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import DeliveryPromiseStatus, MeterDeliveryStatus
from app.models.reading import MeterReading

class DeliveryPromiseRequest(BaseModel):
    meter_mrids: list[str] = Field(description="Meter mRIDs to collect readings from")
    start: datetime
    end: datetime
    reading_type_mrid: str | None = None
    validated_only: bool = False

class MeterDeliveryResult(BaseModel):
    meter_mrid: str
    status: MeterDeliveryStatus
    readings: list[MeterReading] | None = None
    failure_reason: str | None = None

class DeliveryPromise(BaseModel):
    promise_id: str
    status: DeliveryPromiseStatus
    created_at: datetime
    estimated_delivery: datetime
    expires_at: datetime
    request: DeliveryPromiseRequest
    meters_total: int
    meters_collected: int
    meters_failed: int
    meter_results: list[MeterDeliveryResult]
    failure_summary: str | None = None
```

---

## 7. Router Specifications

All paths are prefixed with `/api/v1`. Each router is a `fastapi.APIRouter`. All routers except `health.py` use `dependencies=[Depends(require_api_key)]`.

The backend facade is accessed via `request.app.state.simulator`.

### 7.1 `routers/health.py` — No auth

```python
@router.get("/health")
async def health_check(request: Request) -> dict:
    simulator = request.app.state.simulator
    return {"status": "healthy", "meter_count": simulator.meter_count, "version": "1.0.0"}
```

### 7.2 `routers/meters.py` — Auth required

```python
@router.get("/meters", response_model=PaginatedResponse[Meter])
async def list_meters(
    request: Request,
    meter_type: MeterType | None = Query(None),
    meter_status: MeterStatus | None = Query(None, alias="status"),
    comm_type: CommunicationType | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[Meter]:
    # Filter simulator.get_meters().values() by meter_type, meter_status, comm_type
    # Apply each filter only if the parameter is not None
    # Paginate: items = filtered[offset:offset+limit], total = len(filtered)
    ...

@router.get("/meters/{meter_id}", response_model=Meter)
async def get_meter(request: Request, meter_id: str) -> Meter:
    # simulator.get_meter(meter_id) or raise HTTPException(404, "Meter not found: {meter_id}")
    ...
```

### 7.3 `routers/readings.py` — Auth required

```python
@router.get("/meters/{meter_id}/readings", response_model=PaginatedResponse[MeterReading])
async def get_meter_readings(
    request: Request,
    meter_id: str,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    reading_type_mrid: str | None = Query(None),
    validated_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[MeterReading]:
    # Verify meter exists (404 if not)
    # simulator.get_meter_readings(meter_id, start, end, reading_type_mrid, validated_only)
    # Paginate
    ...

@router.get("/interval-blocks", response_model=PaginatedResponse[IntervalBlock])
async def get_interval_blocks(
    request: Request,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    meter_mrids: str | None = Query(None),    # Comma-separated string
    reading_type_mrid: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[IntervalBlock]:
    # Parse meter_mrids: split on "," and strip whitespace, or default to all meter keys
    # For each meter mrid, call simulator.get_meter_readings(mrid, start, end, reading_type_mrid)
    # Flatten: collect all interval_blocks from all readings into a single list
    # Paginate the flat list
    ...
```

### 7.4 `routers/usage_points.py` — Auth required

```python
@router.get("/usage-points", response_model=PaginatedResponse[UsagePoint])
async def list_usage_points(
    request: Request,
    connection_state: ConnectionState | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[UsagePoint]:
    # Filter simulator.get_usage_points().values() by connection_state if provided
    # Paginate
    ...

@router.get("/usage-points/{usage_point_id}", response_model=UsagePoint)
async def get_usage_point(request: Request, usage_point_id: str) -> UsagePoint:
    # simulator.get_usage_point(usage_point_id) or raise 404
    ...

@router.get("/usage-points/{usage_point_id}/meter-readings",
            response_model=PaginatedResponse[MeterReading])
async def get_usage_point_readings(
    request: Request,
    usage_point_id: str,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[MeterReading]:
    # Lookup usage_point (404 if not found)
    # For each meter_mrid in usage_point.meter_mrids:
    #     readings.extend(simulator.get_meter_readings(meter_mrid, start, end))
    # Paginate combined list
    ...
```

### 7.5 `routers/reading_types.py` — Auth required

```python
@router.get("/reading-types", response_model=PaginatedResponse[ReadingType])
async def list_reading_types(request: Request) -> PaginatedResponse[ReadingType]:
    # items = list(simulator.get_reading_types().values())
    # Return PaginatedResponse with total=len(items), limit=len(items), offset=0
    # This is a small fixed catalog, no pagination params needed
    ...
```

### 7.6 `routers/analytics.py` — Auth required

```python
from datetime import datetime, timedelta, timezone

def _default_time_range(
    start: datetime | None, end: datetime | None
) -> tuple[datetime, datetime]:
    if end is None:
        end = datetime.now(timezone.utc)
    if start is None:
        start = end - timedelta(days=7)
    return start, end

@router.get("/analytics/demand-summary", response_model=list[DemandSummary])
async def get_demand_summary(
    request: Request,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    meter_mrid: str | None = Query(None),
) -> list[DemandSummary]:
    s, e = _default_time_range(start, end)
    return request.app.state.simulator.get_demand_summary(s, e, meter_mrid)

@router.get("/analytics/voltage-summary", response_model=list[VoltageSummary])
async def get_voltage_summary(
    request: Request,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    meter_mrid: str | None = Query(None),
) -> list[VoltageSummary]:
    s, e = _default_time_range(start, end)
    return request.app.state.simulator.get_voltage_summary(s, e, meter_mrid)

@router.get("/analytics/revenue-protection-alerts",
            response_model=list[RevenueProtectionAlert])
async def get_revenue_protection_alerts(
    request: Request,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
) -> list[RevenueProtectionAlert]:
    s, e = _default_time_range(start, end)
    return request.app.state.simulator.get_revenue_protection_alerts(s, e)
```

### 7.7 `routers/delivery_promises.py` — Auth required (CRITICAL PATH)

```python
@router.post("/delivery-promises", response_model=DeliveryPromise,
             status_code=status.HTTP_201_CREATED)
async def create_delivery_promise(
    request: Request,
    body: DeliveryPromiseRequest,
) -> DeliveryPromise:
    # Validate: body.meter_mrids must not be empty → 422 "meter_mrids must not be empty"
    # Validate: body.start must be < body.end → 422 "start must be before end"
    # Delegate to simulator.create_delivery_promise(body)
    # Return 201
    ...

@router.get("/delivery-promises/{promise_id}", response_model=DeliveryPromise)
async def get_delivery_promise(
    request: Request,
    promise_id: str,
) -> DeliveryPromise:
    # simulator.get_delivery_promise(promise_id)
    # This call triggers lazy resolution — see Section 8
    # Client should call this ONCE at or after estimated_delivery (not a poll)
    # 404 if not found: "Delivery promise not found: {promise_id}"
    ...

@router.delete("/delivery-promises/{promise_id}", response_model=DeliveryPromise)
async def cancel_delivery_promise(
    request: Request,
    promise_id: str,
) -> DeliveryPromise:
    # simulator.cancel_delivery_promise(promise_id)
    # Sets status to "cancelled". Optional client cleanup for expired/unneeded promises.
    # 404 if not found: "Delivery promise not found: {promise_id}"
    ...

@router.get("/delivery-promises", response_model=PaginatedResponse[DeliveryPromise])
async def list_delivery_promises(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[DeliveryPromise]:
    # simulator.list_delivery_promises() returns all promises (each lazily resolved)
    # Paginate
    ...
```

---

## 8. Delivery Promise Backend Logic (Critical)

This is the most complex component. The backend needs a promise store and resolution logic. This section describes the algorithm — implement it in whatever layer owns the `create_delivery_promise` / `get_delivery_promise` methods.

### 8.1 On POST (create)

1. Generate a `promise_id` (UUID prefixed with `dp-`).
2. Record `now = datetime.now(UTC)`.
3. For each `meter_mrid` in the request:
   a. Look up the meter. If unknown, record `{ collection_time: now, will_fail: True, failure_reason: "Unknown meter mRID: {mrid}" }`.
   b. Otherwise, simulate the communication path:
      - Determine `latency` (seconds) by sampling uniformly from the range for the meter's `comm_module.comm_type` (see table below).
      - Determine `will_fail` by sampling against the failure rate for the meter's comm type, **overridden to 80% if `meter.status == "commFailure"`**.
      - If `will_fail`, pick a random failure reason string.
   c. Compute `collection_time = now + timedelta(seconds=latency)`.
   d. Store `{ collection_time, will_fail, failure_reason }` per meter (private timing metadata, not exposed in the API response).
4. Create all `MeterDeliveryResult` entries with status `pending`, readings `None`, failure_reason `None`.
5. Compute `estimated_delivery = now + timedelta(seconds=max_latency + 5.0)` (5-second buffer).
6. Compute `expires_at = estimated_delivery + timedelta(seconds=30.0)` (grace window).
7. Create the `DeliveryPromise` with status `pending`, meters_collected=0, meters_failed=0.
8. Store promise + timing metadata. Return 201.

### 8.2 On GET (single collection at estimated_delivery — NOT a poll)

The client makes **one** GET request at or after `estimated_delivery`. This is not a polling mechanism.

1. Load the promise and its timing metadata.
2. If status is not `pending`, return as-is (already resolved).
3. Record `now = datetime.now(UTC)`.
4. If `now < estimated_delivery`, return as-is (client is early, still pending).
5. If `now > expires_at`, set status to `expired` and return.
6. Resolve all meters in a single pass:
   a. For each meter result still in `pending` status:
      - If `now >= collection_time` for that meter:
        - If `will_fail`: set result status to `failed`, populate `failure_reason`.
        - If success: call the backend to produce readings for `[request.start, request.end]`, set result status to `collected`, populate `readings`. If `request.validated_only`, apply VEE processing to the readings.
7. Count `collected` and `failed` totals.
8. Derive overall promise status:
   - Any meters still `pending` after resolution → `expired` (backend missed its promise)
   - `all failed` → `failed`
   - `all collected` → `completed`
   - `mix of collected + failed` → `partial`
9. Build `failure_summary` if `failed > 0`: `"{failed}/{total} meters failed collection"`.
10. Store updated promise. Return 200.

### 8.2.1 On DELETE (optional cancellation)

1. Load the promise.
2. Set status to `cancelled`.
3. Store and return 200.

### 8.3 Communication Latency Model

| Comm Type | Latency Range (seconds) | Base Failure Rate |
|-----------|-------------------------|-------------------|
| Cellular LTE | 3.0 – 8.0 | 5% |
| RF Mesh | 8.0 – 20.0 | 10% |
| PLC | 12.0 – 25.0 | 15% |

**Override:** Meters with `status == "commFailure"` use **80% failure rate** regardless of comm type.

---

## 9. App Factory (`app/main.py`)

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    # Initialize your backend/simulator here
    # Store on app.state.simulator
    yield

def create_app() -> FastAPI:
    app = FastAPI(title="Meter API for Headend", version="1.0.0", lifespan=lifespan)

    prefix = "/api/v1"
    # Register all routers with prefix:
    # app.include_router(health.router, prefix=prefix)
    # app.include_router(meters.router, prefix=prefix)
    # app.include_router(readings.router, prefix=prefix)
    # app.include_router(usage_points.router, prefix=prefix)
    # app.include_router(reading_types.router, prefix=prefix)
    # app.include_router(analytics.router, prefix=prefix)
    # app.include_router(delivery_promises.router, prefix=prefix)

    # CORS for dashboard
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"http://localhost:{settings.dashboard_port}",
                       f"http://127.0.0.1:{settings.dashboard_port}"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
```

---

## 10. Backend Interface Contract

The API layer communicates with the backend through a single facade object stored on `app.state.simulator`. The facade must expose these methods. Vendors implement this by wrapping their existing HES, MDM, and Analytics systems.

```python
from datetime import datetime
from app.models.analytics import DemandSummary, RevenueProtectionAlert, VoltageSummary
from app.models.delivery_promise import DeliveryPromise, DeliveryPromiseRequest
from app.models.meter import Meter
from app.models.reading import MeterReading, ReadingType
from app.models.usage_point import UsagePoint


class BackendFacade:
    """Interface that the API layer expects from the backend.

    The API layer calls only these methods — it never accesses
    the backend internals directly.
    """

    # --- Meters ---

    def get_meters(self) -> dict[str, Meter]: ...
    def get_meter(self, mrid: str) -> Meter | None: ...

    # --- Usage points ---

    def get_usage_points(self) -> dict[str, UsagePoint]: ...
    def get_usage_point(self, mrid: str) -> UsagePoint | None: ...
    def get_meters_for_usage_point(self, usage_point_mrid: str) -> list[Meter]: ...

    # --- Readings (historical, pre-stored) ---

    def get_meter_readings(
        self,
        meter_mrid: str,
        start: datetime | None = None,
        end: datetime | None = None,
        reading_type_mrid: str | None = None,
        validated_only: bool = False,
    ) -> list[MeterReading]: ...

    # --- Reading types ---

    def get_reading_types(self) -> dict[str, ReadingType]: ...

    # --- Analytics ---

    def get_demand_summary(
        self, start: datetime, end: datetime,
        meter_mrid: str | None = None,
    ) -> list[DemandSummary]: ...

    def get_voltage_summary(
        self, start: datetime, end: datetime,
        meter_mrid: str | None = None,
    ) -> list[VoltageSummary]: ...

    def get_revenue_protection_alerts(
        self, start: datetime, end: datetime,
    ) -> list[RevenueProtectionAlert]: ...

    # --- Delivery promises ---

    def create_delivery_promise(
        self, request: DeliveryPromiseRequest,
    ) -> DeliveryPromise: ...

    def get_delivery_promise(self, promise_id: str) -> DeliveryPromise | None: ...
    # get_delivery_promise triggers lazy resolution on call.
    # Returns expired if past expires_at. Single-call collection, not a poll.

    def cancel_delivery_promise(self, promise_id: str) -> DeliveryPromise | None: ...
    # Sets status to "cancelled". Optional cleanup.

    def list_delivery_promises(self) -> list[DeliveryPromise]: ...

    # --- On-demand readings (called internally by promise resolution) ---

    def get_on_demand_readings(
        self,
        meter_mrid: str,
        start: datetime | None = None,
        end: datetime | None = None,
        reading_type_mrid: str | None = None,
        validated_only: bool = False,
    ) -> list[MeterReading]: ...

    # --- Metadata ---

    @property
    def meter_count(self) -> int: ...
```

---

## 11. Error Response Convention

All errors use the same JSON shape: `{ "detail": "Human-readable message" }`.

| Status | When |
|--------|------|
| `200` | Success |
| `201` | Delivery promise created |
| `401` | Missing or invalid `X-API-Key` |
| `404` | Resource not found (meter, usage point, promise) |
| `422` | Validation error (empty meter_mrids, start >= end) |

---

## 12. Pagination Convention

Every list endpoint returns `PaginatedResponse[T]`:

```json
{ "total": 142, "limit": 20, "offset": 0, "items": [...] }
```

Query parameters: `limit` (int, 1–100, default 20), `offset` (int, >= 0, default 0).

---

## 13. Verification

After implementation, verify with these checks:

```bash
# Health (no auth)
curl http://localhost:8000/api/v1/health
# Expect: {"status":"healthy","meter_count":50,"version":"1.0.0"}

# Auth required
curl http://localhost:8000/api/v1/meters
# Expect: 401

# Meters list
curl -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/v1/meters?limit=2
# Expect: {"total":50,"limit":2,"offset":0,"items":[...]}

# Reading types
curl -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/v1/reading-types
# Expect: PaginatedResponse with 4 reading types

# Delivery promise lifecycle
PROMISE=$(curl -s -X POST \
  -H "X-API-Key: dev-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"meter_mrids":["<any-meter-mrid>"],"start":"2024-01-01T00:00:00Z","end":"2024-01-02T00:00:00Z"}' \
  http://localhost:8000/api/v1/delivery-promises)
echo $PROMISE
# Expect: status "pending"

# Wait for estimated_delivery time, then collect (single call, not a poll)
PID=$(echo $PROMISE | python -c "import sys,json; print(json.load(sys.stdin)['promise_id'])")
EDT=$(echo $PROMISE | python -c "import sys,json; print(json.load(sys.stdin)['estimated_delivery'])")
echo "Wait until $EDT, then collect..."
sleep 30  # approximate wait for estimated_delivery
curl -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/v1/delivery-promises/$PID
# Expect: status is completed|partial|failed|expired (terminal in one call)

# OpenAPI spec auto-generated by FastAPI
curl http://localhost:8000/openapi.json
# Should contain all endpoints and schemas
```
