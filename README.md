# PokeAMI

A CIM-compatible OpenAPI interface to simulated Landis+Gyr Advanced Metering Infrastructure (AMI). PokeAMI provides a practical, runnable reference implementation showing how to retrieve meter readings from AMI infrastructure through a standards-based REST API.

"Poke" the AMI — query meters, collect readings, run analytics, and simulate asynchronous on-demand reads, all backed by realistic generated time-series data.

## Architecture

The implementation simulates three Landis+Gyr components backed by realistic generated data, exposed through a FastAPI OpenAPI 3.1 interface using IEC 61968-9 CIM data models.

**Implementation specifications** for vendors and AI agents:

| Document | Format | Description |
|----------|--------|-------------|
| [OpenAPI & MCP Spec](docs/OPENAPI_MCP_SPEC.md) | Markdown | Vendor-facing spec: REST API design, delivery promise pattern, MCP alternative with coupling analysis |
| [OpenAPI & MCP Spec](docs/OPENAPI_MCP_SPEC.docx) | Word | Same spec as a Word document with rendered Mermaid diagrams |
| [Agent Implementation Spec](docs/AMI_OPENAPI_AGENT_SPEC.md) | Markdown | Machine-readable spec for AI coding agents to auto-implement the API layer |

Full architecture and component diagrams are available as PlantUML sources in [`docs/diagrams/`](docs/diagrams/):

| Diagram | Source | Description |
|---------|--------|-------------|
| System Architecture | [`architecture.puml`](docs/diagrams/architecture.puml) | End-to-end AMI topology: meters, comms, HES, MDM, Analytics, Delivery Manager, API |
| Component Diagram | [`component.puml`](docs/diagrams/component.puml) | API layer and simulator layer with all internal dependencies |
| Get Readings Flow | [`sequence_get_readings.puml`](docs/diagrams/sequence_get_readings.puml) | Sequence diagram for `GET /meters/{id}/readings` with VEE pipeline |
| Delivery Promise Flow | [`sequence_delivery_promise.puml`](docs/diagrams/sequence_delivery_promise.puml) | Sequence diagram for async on-demand read lifecycle |
| Application Startup | [`sequence_startup.puml`](docs/diagrams/sequence_startup.puml) | Startup sequence: fleet generation, data generation, component wiring |
| Use Cases | [`use_case.puml`](docs/diagrams/use_case.puml) | Actor/use-case diagram for Billing, Grid Ops, Analysts, DERMS/Field Ops |

A progressive walkthrough series (8 architecture steps + 2 component steps) is in [`docs/diagrams/walkthrough/`](docs/diagrams/walkthrough/) for training presentations.

To render diagrams locally:

```bash
python demo/render_diagrams.py          # PNG output
python demo/render_diagrams.py --svg    # SVG output
```

## Features

- **CIM-compliant data models** — All entities follow IEC 61968-9:2024 Common Information Model
- **Realistic meter fleet** — 50 meters across 4 Landis+Gyr models with weighted distribution
- **Time-series generation** — 30 days of 15-minute interval data with duck curves, seasonal patterns, and quality injection
- **VEE pipeline** — Validation (range/spike checks), Estimation (linear interpolation), Editing
- **Analytics engine** — Demand summaries, voltage analysis with ANSI C84.1 compliance, revenue protection alerts
- **Delivery promises** — Asynchronous on-demand read requests with simulated communication latency and failure rates
- **Solar simulation** — ~20% of residential meters generate reverse energy flow readings
- **Deterministic seeding** — Reproducible data generation for testing

## Data Models (IEC 61968-9 CIM)

All data models follow the IEC 61968-9:2024 Common Information Model (CIM) standard. Key entities:

- **EndDevice / Meter** — Physical metering device with communication module
- **ReadingType** — Describes the nature of readings (energy, demand, voltage) using CIM coded structure
- **IntervalReading** — Single timestamped measurement with quality annotations
- **IntervalBlock** — Collection of consecutive interval readings
- **MeterReading** — Complete reading set from a meter for a reading type
- **UsagePoint** — Logical point where consumption is measured
- **DeliveryPromise** — Asynchronous on-demand read request with per-meter collection status

## Simulated Meter Types

| Model | Type | Phase | Rated Power | Communication | Distribution |
|-------|------|-------|-------------|---------------|-------------|
| E350 | Residential Basic | 1φ (AN) | 9.6 kW | RF Mesh / PLC | 40% |
| E360 | Residential Advanced | 1φ (AN) | 24 kW | Cellular LTE / RF Mesh | 30% |
| S4x/E650 | C&I Polyphase | 3φ (ABCN) | 96 kW | Cellular LTE / RF Mesh | 20% |
| E660/Revelo | C&I IoT | 3φ (ABCN) | 192 kW | Cellular LTE | 10% |

### Reading Types

| mRID | Kind | Flow | Unit | Description |
|------|------|------|------|-------------|
| `rt-forward-energy-wh` | energy | forward | Wh | Forward active energy (all meters) |
| `rt-reverse-energy-wh` | energy | reverse | Wh | Reverse energy (solar meters only) |
| `rt-demand-w` | demand | forward | W | Instantaneous demand |
| `rt-voltage-v` | voltage | none | V | Voltage measurement |

### Delivery Promise Simulation

On-demand reads simulate realistic communication characteristics per technology:

| Comm Type | Latency Range | Base Failure Rate |
|-----------|---------------|-------------------|
| Cellular LTE | 3–8 seconds | 5% |
| RF Mesh | 8–20 seconds | 10% |
| PLC | 12–25 seconds | 15% |
| COMM_FAILURE meters | — | 80% |

## Prerequisites

- Python 3.13+
- pip

## Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd PokeAMI

# Create and activate virtual environment
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# .venv\Scripts\activate        # Windows CMD
# .venv\Scripts\Activate.ps1    # Windows PowerShell
# source .venv/bin/activate     # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Configure (optional — defaults work out of the box)
cp .env.example .env
# Edit .env as needed
```

## Running the Application

```bash
python main.py
```

On first startup, the simulator generates realistic meter data (50 meters x 30 days of 15-minute intervals). Two servers start on separate ports:

| Service | URL | Description |
|---------|-----|-------------|
| **Swagger UI** | http://localhost:8000/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8000/redoc | Alternative API documentation |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | Machine-readable API spec |
| **Health Check** | http://localhost:8000/api/v1/health | API health (no auth) |
| **Dashboard** | http://localhost:8001/dashboard | Interactive control panel UI |

The API server runs on port 8000 (configurable via `PORT`). The dashboard runs on port 8001 (configurable via `DASHBOARD_PORT`) and makes cross-origin calls to the API server via CORS.

## API Endpoints

All endpoints (except health, simulator status, and dashboard) require the `X-API-Key` header.

### Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check (no auth required) |

### Meters

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/meters` | GET | List meters (filter: `meter_type`, `status`, `comm_type`; paginated) |
| `/api/v1/meters/{meter_id}` | GET | Get meter by mRID |

### Readings

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/meters/{meter_id}/readings` | GET | Get readings (params: `start`, `end`, `reading_type_mrid`, `validated_only`) |
| `/api/v1/interval-blocks` | GET | Cross-meter interval block query (params: `start`, `end`, `meter_mrids`, `reading_type_mrid`) |

### Usage Points

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/usage-points` | GET | List usage points (filter: `connection_state`) |
| `/api/v1/usage-points/{id}` | GET | Get usage point by mRID |
| `/api/v1/usage-points/{id}/meter-readings` | GET | Readings for all meters at a usage point |

### Reading Types

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/reading-types` | GET | List all available reading types |

### Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analytics/demand-summary` | GET | Demand analytics (params: `start`, `end`, `meter_mrid`) |
| `/api/v1/analytics/voltage-summary` | GET | Voltage analytics with ANSI C84.1 compliance |
| `/api/v1/analytics/revenue-protection-alerts` | GET | Revenue protection anomaly alerts |

### Delivery Promises

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/delivery-promises` | POST | Create async on-demand read request (body: `meter_mrids`, `start`, `end`, `reading_type_mrid`, `validated_only`) |
| `/api/v1/delivery-promises/{promise_id}` | GET | Collect results at promised delivery time |
| `/api/v1/delivery-promises/{promise_id}` | DELETE | Cancel an expired or unneeded promise (optional) |
| `/api/v1/delivery-promises` | GET | List all delivery promises (paginated) |

### Simulator Control

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/simulator/status` | GET | Component status and event log (no auth required) |
| `/api/v1/simulator/{component}/stop` | POST | Disable a simulator component |
| `/api/v1/simulator/{component}/start` | POST | Enable a simulator component |

### Dashboard

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard` (port 8001) | GET | Interactive control panel UI (no auth required) |

## Endpoint-to-Component Map

Each API endpoint flows through the **SimulatorEngine** facade into one or more underlying components. The table below shows which emulated AMI components are exercised by each endpoint.

**Emulated AMI components** (these represent real Landis+Gyr infrastructure):
- **MeterPark** — Fleet generation and meter/usage-point inventory (emulates physical meter fleet)
- **DataGenerator** — Time-series generation and reading type catalog (emulates meter telemetry)
- **Headend** — Simulated Gridstream HES (raw data collection gateway)
- **MDM** — Simulated Core MDMS with VEE pipeline (Validation, Estimation, Editing)
- **AnalyticsEngine** — Simulated Gridstream Analytics (demand, voltage, revenue protection)
- **DeliveryManager** — Simulated on-demand read promise lifecycle with comm latency

| Endpoint | MeterPark | DataGen | Headend | MDM | Analytics | Delivery Mgr |
|----------|:---------:|:-------:|:-------:|:---:|:---------:|:------------:|
| `GET /health` | x | | x | | | |
| `GET /meters` | x | | x | | | |
| `GET /meters/{id}` | x | | x | | | |
| `GET /meters/{id}/readings` | | | x | x* | | |
| `GET /interval-blocks` | x* | | x | | | |
| `GET /usage-points` | x | | x | | | |
| `GET /usage-points/{id}` | x | | x | | | |
| `GET /usage-points/{id}/meter-readings` | x | | x | | | |
| `GET /reading-types` | | x | x | | | |
| `GET /analytics/demand-summary` | x | | x | | x | |
| `GET /analytics/voltage-summary` | x | | x | | x | |
| `GET /analytics/revenue-protection-alerts` | x | | x | | x | |
| `POST /delivery-promises` | x | | x | x* | | x |
| `GET /delivery-promises/{id}` | x | | x | x* | | x |
| `GET /delivery-promises` | x | | x | x* | | x |

**Legend:**
- **x** — always involved
- **x*** — conditionally involved (`MDM` only when `validated_only=True`; `MeterPark` only when no meter filter is specified)

**Data flow summary:**

- **Meter & usage-point queries** flow through Headend → MeterPark (inventory lookup).
- **Reading queries** flow through Headend for raw data, or Headend → MDM when `validated_only=True` triggers the VEE pipeline.
- **Reading types** flow through Headend → DataGenerator (the catalog of measurement types).
- **Analytics** flow through AnalyticsEngine, which pulls raw readings from Headend and aggregates them.
- **Delivery promises** are managed by DeliveryManager, which simulates communication latency and collects readings from Headend (or MDM) as each meter's simulated response arrives.

### Simulation-only endpoints

The following endpoints are **not part of the emulated AMI architecture**. They exist solely to control the simulation for testing and demonstration purposes, allowing you to stop/start individual components and view the simulator's internal event log from the dashboard.

| Endpoint | Description |
|----------|-------------|
| `GET /simulator/status` | Returns enabled/disabled state for each component and recent EventLog entries |
| `POST /simulator/{component}/stop` | Disables a component (makes its data unavailable) |
| `POST /simulator/{component}/start` | Re-enables a component |
| `GET /dashboard` (port 8001) | Interactive control panel UI — uses all of the above |

These use the **EventLog** (an internal ring buffer), which is simulation scaffolding with no real-world AMI equivalent.

## Authentication

Include the `X-API-Key` header in all requests (except `/api/v1/health`):

```bash
curl -H "X-API-Key: dev-api-key-change-me" http://localhost:8000/api/v1/meters
```

## Example Requests

```bash
# Health check (no auth)
curl http://localhost:8000/api/v1/health

# List all meters
curl -H "X-API-Key: dev-api-key-change-me" http://localhost:8000/api/v1/meters

# Get a specific meter
curl -H "X-API-Key: dev-api-key-change-me" http://localhost:8000/api/v1/meters/{meter_id}

# Get validated readings for a meter
curl -H "X-API-Key: dev-api-key-change-me" \
  "http://localhost:8000/api/v1/meters/{meter_id}/readings?reading_type_mrid=rt-forward-energy-wh&validated_only=true"

# Get demand analytics
curl -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/v1/analytics/demand-summary

# List reading types
curl -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/v1/reading-types

# Create an on-demand read request
curl -X POST -H "X-API-Key: dev-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"meter_mrids": ["meter-001"], "start": "2025-01-01T00:00:00Z", "end": "2025-01-02T00:00:00Z"}' \
  http://localhost:8000/api/v1/delivery-promises

# Collect results at estimated_delivery time
curl -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/v1/delivery-promises/{promise_id}
```

## Demo Scripts

The `demo/` directory contains scripts for exercising and demonstrating the API:

```bash
# Full API demo — starts the server and exercises every endpoint
python demo/run_demo.py

# CNI client demo — polls the API with known meter mRIDs
python demo/cni_demo.py --cycles 5

# Render PlantUML architecture diagrams to PNG/SVG
python demo/render_diagrams.py --svg --online
```

A training video script is available at `demo/TRAINING_VIDEO_SCRIPT.md` for utility integration engineers.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run by category
pytest tests/test_models.py -v              # CIM model validation
pytest tests/test_headend.py -v             # Headend simulator
pytest tests/test_mdm.py -v                 # MDM/VEE pipeline
pytest tests/test_analytics.py -v           # Analytics engine
pytest tests/test_delivery_promises.py -v   # Delivery manager
pytest tests/test_auth.py -v                # Authentication
pytest tests/test_api_meters.py -v          # Meter API endpoints
pytest tests/test_api_readings.py -v        # Reading API endpoints
pytest tests/test_api_usage_points.py -v    # Usage point API endpoints
pytest tests/test_api_reading_types.py -v   # Reading type API endpoints
pytest tests/test_api_analytics.py -v       # Analytics API endpoints
pytest tests/test_api_delivery_promises.py -v  # Delivery promise API endpoints
pytest tests/test_e2e.py -v                 # End-to-end flows
```

Tests use a small dataset (5 meters, 3 days) with a deterministic seed for fast, reproducible execution.

## Configuration

Environment variables (set in `.env` or environment):

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `dev-api-key-change-me` | API authentication key |
| `METER_COUNT` | `50` | Number of simulated meters |
| `DATA_DAYS` | `30` | Days of historical data to generate |
| `INTERVAL_MINUTES` | `15` | Interval between readings in minutes |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | API server port |
| `DASHBOARD_PORT` | `8001` | Dashboard server port |

## Standards References

This implementation references the following standards and resources. See [BIBLIOGRAPHY.md](BIBLIOGRAPHY.md) for the complete bibliography.

- **IEC 61968-9:2024** — Meter Reading and Control (CIM data models)
- **IEC 61970-301** — CIM Base (core packages, mRID, UnitSymbol)
- **ANSI C84.1** — Voltage ratings and Range A compliance
- **TC57CIM** — Open-source CIM reference implementation
- **CIMug** — CIM Users Group standards artifacts

## Project Structure

```
PokeAMI/
├── main.py                    # Entry point (runs API + dashboard servers)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── BIBLIOGRAPHY.md            # Complete standards bibliography
├── app/
│   ├── config.py              # Settings via pydantic-settings
│   ├── auth.py                # API key authentication
│   ├── main.py                # FastAPI API app factory + lifespan
│   ├── dashboard_app.py       # Standalone dashboard app (port 8001)
│   ├── models/                # CIM data models (Pydantic)
│   │   ├── enums.py           # CIM enumerations
│   │   ├── common.py          # DateTimeInterval, pagination
│   │   ├── meter.py           # EndDevice, Meter, CommModule
│   │   ├── reading.py         # ReadingType, IntervalReading, MeterReading
│   │   ├── usage_point.py     # UsagePoint
│   │   ├── analytics.py       # DemandSummary, VoltageSummary, alerts
│   │   └── delivery_promise.py # DeliveryPromise, MeterDeliveryResult
│   ├── routers/               # API endpoint handlers
│   │   ├── health.py          # Health check
│   │   ├── meters.py          # Meter endpoints
│   │   ├── readings.py        # Reading endpoints
│   │   ├── usage_points.py    # Usage point endpoints
│   │   ├── reading_types.py   # Reading type endpoints
│   │   ├── analytics.py       # Analytics endpoints
│   │   ├── delivery_promises.py # Delivery promise endpoints
│   │   ├── simulator.py       # Simulator control endpoints
│   │   └── dashboard.py       # Dashboard HTML SPA
│   └── simulator/             # Simulated L+G components
│       ├── __init__.py        # SimulatorEngine facade
│       ├── meter_park.py      # Fleet generation
│       ├── data_generator.py  # Time-series generation
│       ├── headend.py         # Simulated Gridstream HES
│       ├── mdm.py             # Simulated MDM with VEE
│       ├── analytics_engine.py # Analytics platform
│       ├── delivery_manager.py # On-demand read simulation
│       └── event_log.py       # Simulator event log
├── tests/                     # Test suite
│   ├── conftest.py            # Shared fixtures
│   └── test_*.py              # Test modules (13 files)
├── demo/                      # Demo & training scripts
│   ├── run_demo.py            # Full API demo runner
│   ├── cni_demo.py            # CNI client polling demo
│   ├── render_diagrams.py     # PlantUML diagram renderer
│   └── TRAINING_VIDEO_SCRIPT.md # Training video walkthrough
└── docs/
    ├── OPENAPI_MCP_SPEC.md    # Vendor-facing OpenAPI/MCP specification
    ├── OPENAPI_MCP_SPEC.docx  # Word version with rendered diagrams
    ├── AMI_OPENAPI_AGENT_SPEC.md # Machine-readable agent implementation spec
    ├── build_docx.py          # Script to rebuild the Word document
    └── diagrams/              # PlantUML architecture diagrams
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13 |
| Framework | FastAPI (OpenAPI 3.1) |
| Models | Pydantic v2 |
| Config | pydantic-settings + .env |
| Testing | pytest + httpx (TestClient) |
| Server | uvicorn |

## License

This project is provided as a reference implementation for educational purposes.
