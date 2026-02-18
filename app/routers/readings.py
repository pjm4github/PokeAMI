"""Reading endpoints - meter readings and interval blocks.

References:
    - IEC 61968-9:2024, Section 6.3 "Meter Reading Model"
    - CIM REST API patterns for reading queries
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth import require_api_key
from app.models.common import PaginatedResponse
from app.models.reading import IntervalBlock, MeterReading

router = APIRouter(tags=["Readings"], dependencies=[Depends(require_api_key)])


@router.get("/meters/{meter_id}/readings", response_model=PaginatedResponse[MeterReading])
async def get_meter_readings(
    request: Request,
    meter_id: str,
    start: datetime | None = Query(None, description="Start of time range (ISO 8601)"),
    end: datetime | None = Query(None, description="End of time range (ISO 8601)"),
    reading_type_mrid: str | None = Query(None, description="Filter by reading type mRID"),
    validated_only: bool = Query(False, description="Return only VEE-validated readings"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
) -> PaginatedResponse[MeterReading]:
    """Get readings for a specific meter with optional filtering.

    Supports time range, reading type, and validation status filters.
    Set validated_only=true to get VEE-processed readings.
    """
    simulator = request.app.state.simulator
    meter = simulator.get_meter(meter_id)
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meter not found: {meter_id}",
        )

    readings = simulator.get_meter_readings(
        meter_id, start, end, reading_type_mrid, validated_only
    )

    total = len(readings)
    items = readings[offset : offset + limit]

    return PaginatedResponse[MeterReading](
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/interval-blocks", response_model=PaginatedResponse[IntervalBlock])
async def get_interval_blocks(
    request: Request,
    start: datetime | None = Query(None, description="Start of time range (ISO 8601)"),
    end: datetime | None = Query(None, description="End of time range (ISO 8601)"),
    meter_mrids: str | None = Query(
        None, description="Comma-separated list of meter mRIDs"
    ),
    reading_type_mrid: str | None = Query(None, description="Filter by reading type mRID"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
) -> PaginatedResponse[IntervalBlock]:
    """Query interval blocks across meters.

    Supports filtering by time range, meter mRIDs, and reading type.
    """
    simulator = request.app.state.simulator

    # Parse meter mRIDs
    target_mrids: list[str] = []
    if meter_mrids:
        target_mrids = [m.strip() for m in meter_mrids.split(",")]
    else:
        target_mrids = list(simulator.get_meters().keys())

    all_blocks: list[IntervalBlock] = []
    for mrid in target_mrids:
        readings = simulator.get_meter_readings(
            mrid, start, end, reading_type_mrid
        )
        for reading in readings:
            all_blocks.extend(reading.interval_blocks)

    total = len(all_blocks)
    items = all_blocks[offset : offset + limit]

    return PaginatedResponse[IntervalBlock](
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )
