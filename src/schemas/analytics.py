from datetime import datetime

from pydantic import BaseModel


class EventBookingAnalytics(BaseModel):
    event_id: str
    title: str
    date: datetime
    venue: str
    total_bookings: int
    total_tickets: int


class UserBookingAnalytics(BaseModel):
    user_id: str
    name: str
    email: str
    total_tickets: int


class RevenueAnalytics(BaseModel):
    total_bookings: int
    total_tickets: int
