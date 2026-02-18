"""Delivery Promise models for asynchronous on-demand meter reads.

The delivery promise pattern decouples the request for meter data from its
fulfillment, reflecting the reality that AMI communication networks (RF Mesh,
PLC, Cellular) introduce significant latency and unreliability.

References:
    - IEC 61968-9:2024, Section 9 "Message Exchanges" (async request/reply)
    - Landis+Gyr Gridstream HES on-demand read request workflow
    - Landis+Gyr Command Center async job status model
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import DeliveryPromiseStatus, MeterDeliveryStatus
from app.models.reading import MeterReading


class DeliveryPromiseRequest(BaseModel):
    """Client request specifying which meters and time range to collect.

    References:
        - IEC 61968-9:2024, MeterReadSchedule (on-demand read request)
    """

    meter_mrids: list[str] = Field(description="Meter mRIDs to collect readings from")
    start: datetime = Field(description="Start of requested time range (UTC)")
    end: datetime = Field(description="End of requested time range (UTC)")
    reading_type_mrid: str | None = Field(
        default=None, description="Optional reading type filter"
    )
    validated_only: bool = Field(
        default=False, description="If true, return only VEE-validated readings"
    )


class MeterDeliveryResult(BaseModel):
    """Per-meter collection result within a delivery promise.

    References:
        - Landis+Gyr Gridstream HES per-device read status
    """

    meter_mrid: str = Field(description="Meter mRID")
    status: MeterDeliveryStatus = Field(description="Collection status for this meter")
    readings: list[MeterReading] | None = Field(
        default=None, description="Collected readings (null if not yet collected)"
    )
    failure_reason: str | None = Field(
        default=None, description="Reason for collection failure (null if not failed)"
    )


class DeliveryPromise(BaseModel):
    """An asynchronous delivery promise for on-demand meter reads.

    Tracks the lifecycle of a batch meter read request from creation
    through collection to completion (or partial/failed).

    References:
        - IEC 61968-9:2024, Section 9 "Message Exchanges"
        - Landis+Gyr Command Center async job model
    """

    promise_id: str = Field(description="Unique identifier for this delivery promise")
    status: DeliveryPromiseStatus = Field(description="Overall promise status")
    created_at: datetime = Field(description="When the promise was created (UTC)")
    estimated_delivery: datetime = Field(
        description="Estimated time when all data should be available (UTC)"
    )
    request: DeliveryPromiseRequest = Field(description="Original request parameters")
    meters_total: int = Field(description="Total meters in the request")
    meters_collected: int = Field(description="Meters successfully collected so far")
    meters_failed: int = Field(description="Meters that failed collection")
    meter_results: list[MeterDeliveryResult] = Field(
        description="Per-meter collection results"
    )
    failure_summary: str | None = Field(
        default=None, description="Summary of failures (null if none)"
    )
