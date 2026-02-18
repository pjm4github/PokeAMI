"""Delivery Promise endpoints - async on-demand meter read requests.

Implements the delivery promise pattern for slow/unreliable AMI networks:
1. POST to create a promise (meter mRIDs + date range)
2. GET to poll for results (status evolves over time)

References:
    - IEC 61968-9:2024, Section 9 "Message Exchanges" (async patterns)
    - Landis+Gyr Gridstream HES on-demand read workflow
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth import require_api_key
from app.models.common import PaginatedResponse
from app.models.delivery_promise import DeliveryPromise, DeliveryPromiseRequest

router = APIRouter(tags=["Delivery Promises"], dependencies=[Depends(require_api_key)])


@router.post(
    "/delivery-promises",
    response_model=DeliveryPromise,
    status_code=status.HTTP_201_CREATED,
)
async def create_delivery_promise(
    request: Request,
    body: DeliveryPromiseRequest,
) -> DeliveryPromise:
    """Create a new delivery promise for on-demand meter reads.

    Accepts a list of meter mRIDs and a date range. Returns a promise
    with an estimated delivery time. Poll the promise by ID to retrieve
    data as it becomes available.
    """
    if not body.meter_mrids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="meter_mrids must not be empty",
        )
    if body.start >= body.end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="start must be before end",
        )

    simulator = request.app.state.simulator
    promise = simulator.create_delivery_promise(body)
    return promise


@router.get("/delivery-promises/{promise_id}", response_model=DeliveryPromise)
async def get_delivery_promise(
    request: Request,
    promise_id: str,
) -> DeliveryPromise:
    """Retrieve a delivery promise by ID.

    Each GET resolves the current state based on wall-clock time:
    - Before estimated delivery, collection ongoing: inProgress
    - All meters collected: completed
    - Past deadline, some failures: partial
    - Past deadline, all failed: failed
    """
    simulator = request.app.state.simulator
    promise = simulator.get_delivery_promise(promise_id)
    if not promise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery promise not found: {promise_id}",
        )
    return promise


@router.get("/delivery-promises", response_model=PaginatedResponse[DeliveryPromise])
async def list_delivery_promises(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
) -> PaginatedResponse[DeliveryPromise]:
    """List all delivery promises with pagination."""
    simulator = request.app.state.simulator
    promises = simulator.list_delivery_promises()

    total = len(promises)
    items = promises[offset : offset + limit]

    return PaginatedResponse[DeliveryPromise](
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )
