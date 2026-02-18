# MeterAPIforHeadend

## Project Overview
CIM-compatible OpenAPI interface to simulated Landis+Gyr AMI (Advanced Metering Infrastructure). Provides a reference implementation for retrieving meter readings through a standards-based REST API using IEC 61968-9 CIM data models.

Simulates three L+G components: Gridstream HES (headend), Core MDMS (with VEE pipeline), and Gridstream Analytics — backed by realistic generated time-series data for 50 meters across 30 days.

## Tech Stack
- **Language:** Python 3.13
- **Framework:** FastAPI (OpenAPI 3.1)
- **Models:** Pydantic v2
- **Config:** pydantic-settings + .env
- **Testing:** pytest + httpx (TestClient)
- **Server:** uvicorn
- **Virtual Environment:** `.venv/` (virtualenv)

## Project Structure
```
app/
├── config.py              # Settings (pydantic-settings)
├── auth.py                # X-API-Key authentication
├── main.py                # FastAPI app factory + lifespan
├── models/                # CIM Pydantic models
│   ├── enums.py           # CIM enumerations
│   ├── common.py          # DateTimeInterval, pagination
│   ├── meter.py           # EndDevice, Meter, CommModule
│   ├── reading.py         # ReadingType, IntervalReading, MeterReading
│   ├── usage_point.py     # UsagePoint
│   └── analytics.py       # DemandSummary, VoltageSummary, alerts
├── routers/               # API endpoints
│   ├── health.py          # GET /health (no auth)
│   ├── meters.py          # GET /meters, /meters/{id}
│   ├── readings.py        # GET /meters/{id}/readings, /interval-blocks
│   ├── usage_points.py    # GET /usage-points
│   ├── reading_types.py   # GET /reading-types
│   └── analytics.py       # GET /analytics/*
└── simulator/             # Simulated L+G components
    ├── __init__.py         # SimulatorEngine facade
    ├── meter_park.py       # Fleet generation (E350/E360/S4x/E660)
    ├── data_generator.py   # Time-series with load curves + quality injection
    ├── headend.py          # Simulated Gridstream HES
    ├── mdm.py              # MDM with VEE pipeline
    └── analytics_engine.py # Demand, voltage, revenue protection
tests/                     # pytest test suite
docs/diagrams/             # PlantUML diagrams
```

## Development Setup
```bash
# Activate virtual environment
source .venv/Scripts/activate   # Windows Git Bash
# .venv\Scripts\activate        # Windows CMD
# .venv\Scripts\Activate.ps1    # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

## Commands
```bash
# Run the application
python main.py

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api_meters.py -v

# Lint
ruff check .
```

## Conventions
- Use Python type hints throughout
- Follow PEP 8 style guidelines
- CIM models include docstrings with IEC/TC57CIM references
- All datetimes are timezone-aware UTC
- snake_case JSON (Python-friendly)
- Inline bibliography references in every model/simulator file

## Architecture
- **In-memory data** — No database; Python dicts keyed by mRID
- **Deterministic seeding** — DataGenerator accepts optional seed for reproducible test data
- **Dependency injection** — Simulator on `app.state`, accessed via FastAPI `Depends()`
- **Session-scoped test fixtures** — 5 meters, 3 days for fast tests
- **VEE Pipeline** — Validation (range/spike) → Estimation (linear interpolation) → Editing
- **Data flow:** MeterPark → DataGenerator → Headend → MDM → Analytics → API

## Key Files
- `main.py` — Entry point (uvicorn runner)
- `app/main.py` — FastAPI app factory with lifespan
- `app/simulator/__init__.py` — SimulatorEngine facade (wires all components)
- `app/simulator/data_generator.py` — Most complex: load curves, seasonal, quality injection
- `app/models/reading.py` — Core CIM reading models
- `tests/conftest.py` — Shared fixtures (small dataset, deterministic seed)
- `BIBLIOGRAPHY.md` — Complete standards references
