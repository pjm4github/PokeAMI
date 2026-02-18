"""Common base models and utilities for CIM data structures.

References:
    - IEC 61968-9:2024, DateTimeInterval
    - IEC 61970-301, IdentifiedObject.mRID (UUID-based)
    - TC57CIM: IEC61970/Base/Domain/DateTimeInterval
"""

import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


def generate_mrid() -> str:
    """Generate a CIM-compliant mRID using UUID4.

    References:
        - IEC 61970-301: IdentifiedObject.mRID is typically a UUID
        - CIM Primer Seventh Edition (EPRI 3002021840), Section on mRID usage
    """
    return str(uuid.uuid4())


class DateTimeInterval(BaseModel):
    """A period of time defined by start and end timestamps.

    References:
        - IEC 61970-301, DateTimeInterval
        - TC57CIM: IEC61970/Base/Domain/DateTimeInterval
    """

    start: datetime
    end: datetime


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated API response wrapper."""

    total: int = Field(description="Total number of items available")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")
    items: list[T] = Field(description="Items in the current page")
