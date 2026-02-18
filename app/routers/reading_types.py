"""Reading type endpoints.

References:
    - IEC 61968-9:2024, ReadingType (18 coded attributes)
    - PNNL-34946, Section 4.3 "ReadingType Structure"
"""

from fastapi import APIRouter, Depends, Request

from app.auth import require_api_key
from app.models.common import PaginatedResponse
from app.models.reading import ReadingType

router = APIRouter(tags=["Reading Types"], dependencies=[Depends(require_api_key)])


@router.get("/reading-types", response_model=PaginatedResponse[ReadingType])
async def list_reading_types(
    request: Request,
) -> PaginatedResponse[ReadingType]:
    """List all available reading types.

    Returns the catalog of reading types supported by the simulated AMI system.
    Each reading type describes the nature of the measurement (energy, demand,
    voltage, etc.) using CIM-standard coded attributes.
    """
    simulator = request.app.state.simulator
    reading_types = list(simulator.get_reading_types().values())

    return PaginatedResponse[ReadingType](
        total=len(reading_types),
        limit=len(reading_types),
        offset=0,
        items=reading_types,
    )
