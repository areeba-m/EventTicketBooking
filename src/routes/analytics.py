from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pymongo.collection import Collection

from src.db.collections import bookings_collection, events_collection, users_collection
from src.dependencies.auth import require_role
from src.schemas.analytics import EventBookingAnalytics, RevenueAnalytics, UserBookingAnalytics
from src.schemas.users import UserRole
from src.services import analytics as analytics_service

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_role(UserRole.ORGANIZER))],
)


@router.get("/events", response_model=list[EventBookingAnalytics])
def event_analytics(
    bookings: Annotated[Collection, Depends(bookings_collection)],
    events: Annotated[Collection, Depends(events_collection)],
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    venue: str | None = Query(default=None, min_length=1, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    return analytics_service.event_booking_analytics(
        bookings,
        events,
        start_date=start_date,
        end_date=end_date,
        venue=venue,
        skip=skip,
        limit=limit,
    )


@router.get("/users", response_model=list[UserBookingAnalytics])
def user_analytics(
    bookings: Annotated[Collection, Depends(bookings_collection)],
    users: Annotated[Collection, Depends(users_collection)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    return analytics_service.user_booking_analytics(bookings, users, skip=skip, limit=limit)


@router.get("/revenue", response_model=RevenueAnalytics)
def revenue_analytics(
    bookings: Annotated[Collection, Depends(bookings_collection)],
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
) -> dict:
    return analytics_service.revenue_analytics(
        bookings,
        start_date=start_date,
        end_date=end_date,
    )
