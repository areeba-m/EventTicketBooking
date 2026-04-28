from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.bookings import BookingSummary


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    date: datetime
    venue: str = Field(min_length=1, max_length=200)
    total_seats: int = Field(ge=1)


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    date: datetime | None = None
    venue: str | None = Field(default=None, min_length=1, max_length=200)
    total_seats: int | None = Field(default=None, ge=1)


class EventPublic(BaseModel):
    id: str
    title: str
    date: datetime
    venue: str
    total_seats: int
    available_seats: int
    bookings: list[BookingSummary] = Field(default_factory=list)
