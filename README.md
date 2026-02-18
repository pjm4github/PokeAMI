# Meter API for Headend

A CIM-compatible OpenAPI interface to simulated Landis+Gyr Advanced Metering Infrastructure (AMI). This project provides a practical, runnable reference implementation showing how to retrieve meter readings from AMI infrastructure through a standards-based REST API.

## Architecture

The implementation simulates three Landis+Gyr components backed by realistic generated data, exposed through a FastAPI OpenAPI 3.1 interface using IEC 61968-9 CIM data models.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Applications                         │
│               (Swagger UI / curl / Utility Systems)                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST API (OpenAPI 3.1)
                               │ X-API-Key Authentication
┌──────────────────────────────▼──────────────────────────────────────┐
│                     FastAPI Application Layer                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ /meters  │ │/readings │ │/usage-points │ │   /analytics     │   │
│  └────┬─────┘ └────┬─────┘ └──────┬───────┘ └────────┬─────────┘   │
└───────┼─────────────┼──────────────┼──────────────────┼─────────────┘
        │             │              │                  │
┌───────▼─────────────▼──────────────▼──────────────────▼─────────────┐
│                       Simulator Engine                               │
│                                                                      │
│  ┌──────────────────┐  ┌────────────────┐  ┌──────────────────────┐  │
│  │   Gridstream HES │  │   Core MDMS    │  │  Gridstream Analytics│  │
│  │   (Headend)      │  │   (VEE)        │  │  (Demand/Voltage)   │  │
│  │                  │  │                │  │                      │  │
│  │  Raw data        │  │  Validation    │  │  Demand summary      │  │
│  │  collection      │──▶  Estimation    │  │  Voltage analysis    │  │
│  │                  │  │  Editing       │  │  Revenue protection  │  │
│  └────────┬─────────┘  └────────────────┘  └──────────────────────┘  │
│           │                                                          │
│  ┌────────▼─────────┐  ┌────────────────┐                            │
│  │    Meter Park     │  │ Data Generator │                            │
│  │  (Fleet Mgmt)    │◀─│ (Time Series)  │                            │
│  └──────────────────┘  └────────────────┘                            │
└──────────────────────────────────────────────────────────────────────┘
```

## Data Models (IEC 61968-9 CIM)

All data models follow the IEC 61968-9:2024 Common Information Model (CIM) standard. Key entities:

- **EndDevice / Meter** — Physical metering device with communication module
- **ReadingType** — Describes the nature of readings (energy, demand, voltage) using CIM 18-attribute coded structure
- **IntervalReading** — Single timestamped measurement with quality annotations
- **IntervalBlock** — Collection of consecutive interval readings
- **MeterReading** — Complete reading set from a meter for a reading type
- **UsagePoint** — Logical point where consumption is measured

## Simulated Meter Types

| Model | Type | Phase | Rated Power | Communication | Distribution |
|-------|------|-------|-------------|---------------|-------------|
| E350 | Residential Basic | 1φ (AN) | 9.6 kW | RF Mesh / PLC | 40% |
| E360 | Residential Advanced | 1φ (AN) | 24 kW | Cellular LTE / RF Mesh | 30% |
| S4x/E650 | C&I Polyphase | 3φ (ABCN) | 96 kW | Cellular LTE / RF Mesh | 20% |
| E660/Revelo | C&I IoT | 3φ (ABCN) | 192 kW | Cellular LTE | 10% |

## Prerequisites

- Python 3.13+
- pip

## Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd MeterAPIforHeadend

# Create and activate virtual environment
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# .venv\Scripts\activate        # Windows CMD
# .venv\Scripts\Activate.ps1    # Windows PowerShell
# source .venv/bin/activate     # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Configure (optional - defaults work out of the box)
cp .env.example .env
# Edit .env as needed
```

## Running the Application

```bash
python main.py
```

The server starts on `http://localhost:8000` by default. On first startup, the simulator generates realistic meter data (50 meters × 30 days of 15-minute intervals).

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

## API Endpoints

All endpoints (except health) require the `X-API-Key` header.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check (no auth required) |
| `/api/v1/meters` | GET | List meters (filter: type, status, comm_type) |
| `/api/v1/meters/{meter_id}` | GET | Get meter by mRID |
| `/api/v1/meters/{meter_id}/readings` | GET | Get readings (params: start, end, reading_type_mrid, validated_only) |
| `/api/v1/usage-points` | GET | List usage points (filter: connection_state) |
| `/api/v1/usage-points/{id}` | GET | Get usage point by mRID |
| `/api/v1/usage-points/{id}/meter-readings` | GET | Readings for all meters at usage point |
| `/api/v1/reading-types` | GET | List all available reading types |
| `/api/v1/interval-blocks` | GET | Query interval blocks (params: start, end, meter_mrids, reading_type_mrid) |
| `/api/v1/analytics/demand-summary` | GET | Demand analytics (params: start, end, meter_mrid) |
| `/api/v1/analytics/voltage-summary` | GET | Voltage analytics (params: start, end, meter_mrid) |
| `/api/v1/analytics/revenue-protection-alerts` | GET | Revenue protection alerts |

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

# Get readings for a meter (with optional filters)
curl -H "X-API-Key: dev-api-key-change-me" \
  "http://localhost:8000/api/v1/meters/{meter_id}/readings?reading_type_mrid=rt-forward-energy-wh&validated_only=true"

# Get demand analytics
curl -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/v1/analytics/demand-summary

# List reading types
curl -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/v1/reading-types
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_models.py -v          # CIM model validation
pytest tests/test_headend.py -v         # Headend simulator
pytest tests/test_mdm.py -v            # MDM/VEE pipeline
pytest tests/test_analytics.py -v       # Analytics engine
pytest tests/test_api_meters.py -v      # Meter API endpoints
pytest tests/test_auth.py -v            # Authentication
pytest tests/test_e2e.py -v             # End-to-end flows
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
| `PORT` | `8000` | Server port |

## Standards References

This implementation references the following standards and resources. See [BIBLIOGRAPHY.md](BIBLIOGRAPHY.md) for the complete bibliography.

- **IEC 61968-9:2024** — Meter Reading and Control (CIM data models)
- **IEC 61970-301** — CIM Base (core packages, mRID, UnitSymbol)
- **ANSI C84.1** — Voltage ratings and Range A compliance
- **TC57CIM** — Open-source CIM reference implementation
- **CIMug** — CIM Users Group standards artifacts

## Project Structure

```
MeterAPIforHeadend/
├── main.py                    # Entry point (uvicorn runner)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── BIBLIOGRAPHY.md            # Complete standards bibliography
├── app/
│   ├── config.py              # Settings via pydantic-settings
│   ├── auth.py                # API key authentication
│   ├── main.py                # FastAPI app factory + lifespan
│   ├── models/                # CIM data models (Pydantic)
│   │   ├── enums.py           # CIM enumerations
│   │   ├── common.py          # DateTimeInterval, pagination
│   │   ├── meter.py           # EndDevice, Meter, CommModule
│   │   ├── reading.py         # ReadingType, IntervalReading, MeterReading
│   │   ├── usage_point.py     # UsagePoint
│   │   └── analytics.py       # DemandSummary, VoltageSummary, alerts
│   ├── routers/               # API endpoint handlers
│   │   ├── health.py          # Health check
│   │   ├── meters.py          # Meter endpoints
│   │   ├── readings.py        # Reading endpoints
│   │   ├── usage_points.py    # Usage point endpoints
│   │   ├── reading_types.py   # Reading type endpoints
│   │   └── analytics.py       # Analytics endpoints
│   └── simulator/             # Simulated L+G components
│       ├── __init__.py        # SimulatorEngine facade
│       ├── meter_park.py      # Fleet generation
│       ├── data_generator.py  # Time-series generation
│       ├── headend.py         # Simulated Gridstream HES
│       ├── mdm.py             # Simulated MDM with VEE
│       └── analytics_engine.py # Analytics platform
├── tests/                     # Test suite
│   ├── conftest.py            # Shared fixtures
│   └── test_*.py              # Test modules
└── docs/
    └── diagrams/              # PlantUML architecture diagrams
```

## License

This project is provided as a reference implementation for educational purposes.
