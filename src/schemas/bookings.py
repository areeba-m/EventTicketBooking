from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class BookingStatus(StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class BookingSummary(BaseModel):
    booking_id: str
    event_id: str
    seats: int = Field(ge=1)
    status: BookingStatus


class BookingCreate(BaseModel):
    event_id: str
    seats: int = Field(ge=1)


class BookingPublic(BaseModel):
    id: str
    user_id: str
    event_id: str
    seats: int
    status: BookingStatus
    created_at: datetime
