"""Usage point endpoints.

References:
    - IEC 61968-9:2024, Section 6.5 "Usage Point"
    - TC57CIM: IEC61968/Metering/UsagePoint.py
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth import require_api_key
from app.models.common import PaginatedResponse
from app.models.enums import ConnectionState
from app.models.reading import MeterReading
from app.models.usage_point import UsagePoint

router = APIRouter(tags=["Usage Points"], dependencies=[Depends(require_api_key)])


@router.get("/usage-points", response_model=PaginatedResponse[UsagePoint])
async def list_usage_points(
    request: Request,
    connection_state: ConnectionState | None = Query(
        None, description="Filter by connection state"
    ),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
) -> PaginatedResponse[UsagePoint]:
    """List all usage points with optional filtering."""
    simulator = request.app.state.simulator
    usage_points = list(simulator.get_usage_points().values())

    if connection_state is not None:
        usage_points = [
            up for up in usage_points if up.connection_state == connection_state
        ]

    total = len(usage_points)
    items = usage_points[offset : offset + limit]

    return PaginatedResponse[UsagePoint](
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/usage-points/{usage_point_id}", response_model=UsagePoint)
async def get_usage_point(
    request: Request,
    usage_point_id: str,
) -> UsagePoint:
    """Get a specific usage point by mRID."""
    simulator = request.app.state.simulator
    up = simulator.get_usage_point(usage_point_id)
    if not up:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usage point not found: {usage_point_id}",
        )
    return up


@router.get(
    "/usage-points/{usage_point_id}/meter-readings",
    response_model=PaginatedResponse[MeterReading],
)
async def get_usage_point_readings(
    request: Request,
    usage_point_id: str,
    start: datetime | None = Query(None, description="Start of time range (ISO 8601)"),
    end: datetime | None = Query(None, description="End of time range (ISO 8601)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
) -> PaginatedResponse[MeterReading]:
    """Get readings for all meters at a usage point."""
    simulator = request.app.state.simulator
    up = simulator.get_usage_point(usage_point_id)
    if not up:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usage point not found: {usage_point_id}",
        )

    all_readings: list[MeterReading] = []
    for meter_mrid in up.meter_mrids:
        readings = simulator.get_meter_readings(meter_mrid, start, end)
        all_readings.extend(readings)

    total = len(all_readings)
    items = all_readings[offset : offset + limit]

    return PaginatedResponse[MeterReading](
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )
