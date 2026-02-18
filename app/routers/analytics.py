"""Analytics endpoints - demand, voltage, and revenue protection.

References:
    - Landis+Gyr Gridstream Analytics Solution Overview (publicly available)
    - ANSI C84.1 - Electric Power Systems and Equipment Voltage Ratings
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request

from app.auth import require_api_key
from app.models.analytics import DemandSummary, RevenueProtectionAlert, VoltageSummary

router = APIRouter(tags=["Analytics"], dependencies=[Depends(require_api_key)])


def _default_time_range(
    start: datetime | None, end: datetime | None
) -> tuple[datetime, datetime]:
    """Provide sensible defaults for time range parameters."""
    if end is None:
        end = datetime.now(timezone.utc)
    if start is None:
        start = end - timedelta(days=7)
    return start, end


@router.get("/analytics/demand-summary", response_model=list[DemandSummary])
async def get_demand_summary(
    request: Request,
    start: datetime | None = Query(None, description="Start of analysis period (ISO 8601)"),
    end: datetime | None = Query(None, description="End of analysis period (ISO 8601)"),
    meter_mrid: str | None = Query(None, description="Specific meter mRID (omit for all)"),
) -> list[DemandSummary]:
    """Get demand analytics summary.

    Returns peak demand, average demand, minimum demand, and load factor
    for the specified period. Can be filtered to a single meter or return
    summaries for all meters.
    """
    simulator = request.app.state.simulator
    s, e = _default_time_range(start, end)
    return simulator.get_demand_summary(s, e, meter_mrid)


@router.get("/analytics/voltage-summary", response_model=list[VoltageSummary])
async def get_voltage_summary(
    request: Request,
    start: datetime | None = Query(None, description="Start of analysis period (ISO 8601)"),
    end: datetime | None = Query(None, description="End of analysis period (ISO 8601)"),
    meter_mrid: str | None = Query(None, description="Specific meter mRID (omit for all)"),
) -> list[VoltageSummary]:
    """Get voltage analytics summary with ANSI C84.1 compliance.

    Returns voltage statistics and the count of intervals that exceeded
    ANSI C84.1 Range A limits (±5% of nominal voltage).

    References:
        - ANSI C84.1 Range A: 114V-126V for 120V nominal
    """
    simulator = request.app.state.simulator
    s, e = _default_time_range(start, end)
    return simulator.get_voltage_summary(s, e, meter_mrid)


@router.get(
    "/analytics/revenue-protection-alerts",
    response_model=list[RevenueProtectionAlert],
)
async def get_revenue_protection_alerts(
    request: Request,
    start: datetime | None = Query(None, description="Start of analysis period (ISO 8601)"),
    end: datetime | None = Query(None, description="End of analysis period (ISO 8601)"),
) -> list[RevenueProtectionAlert]:
    """Get revenue protection alerts.

    Returns alerts for anomalies such as reverse energy flow on non-solar
    meters, consumption anomalies, and tamper detection events.

    References:
        - Landis+Gyr Gridstream Analytics revenue protection capabilities
    """
    simulator = request.app.state.simulator
    s, e = _default_time_range(start, end)
    return simulator.get_revenue_protection_alerts(s, e)
