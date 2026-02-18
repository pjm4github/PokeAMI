"""Meter endpoints - list and retrieve EndDevice/Meter resources.

References:
    - IEC 61968-9:2024, Section 6.2 "End Device Model"
    - CIM REST API patterns
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth import require_api_key
from app.models.common import PaginatedResponse
from app.models.enums import CommunicationType, MeterStatus, MeterType
from app.models.meter import Meter

router = APIRouter(tags=["Meters"], dependencies=[Depends(require_api_key)])


@router.get("/meters", response_model=PaginatedResponse[Meter])
async def list_meters(
    request: Request,
    meter_type: MeterType | None = Query(None, description="Filter by meter type"),
    meter_status: MeterStatus | None = Query(None, alias="status", description="Filter by status"),
    comm_type: CommunicationType | None = Query(None, description="Filter by communication type"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
) -> PaginatedResponse[Meter]:
    """List all meters with optional filtering and pagination.

    Supports filtering by meter type, operational status, and communication type.
    """
    simulator = request.app.state.simulator
    meters = list(simulator.get_meters().values())

    # Apply filters
    if meter_type is not None:
        meters = [m for m in meters if m.meter_type == meter_type]
    if meter_status is not None:
        meters = [m for m in meters if m.status == meter_status]
    if comm_type is not None:
        meters = [m for m in meters if m.comm_module.comm_type == comm_type]

    total = len(meters)
    items = meters[offset : offset + limit]

    return PaginatedResponse[Meter](
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/meters/{meter_id}", response_model=Meter)
async def get_meter(
    request: Request,
    meter_id: str,
) -> Meter:
    """Get a specific meter by its mRID."""
    simulator = request.app.state.simulator
    meter = simulator.get_meter(meter_id)
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meter not found: {meter_id}",
        )
    return meter
