from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from src.dependencies.auth import require_role
from src.schemas.analytics import EventBookingAnalytics, RevenueAnalytics, UserBookingAnalytics
from src.schemas.users import UserRole
from src.services.analytics import AnalyticsService, get_analytics_service

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_role(UserRole.ORGANIZER))],
)


@router.get("/events", response_model=list[EventBookingAnalytics])
async def event_analytics(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    venue: str | None = Query(default=None, min_length=1, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    return await service.event_booking_analytics(
        start_date=start_date,
        end_date=end_date,
        venue=venue,
        skip=skip,
        limit=limit,
    )


@router.get("/users", response_model=list[UserBookingAnalytics])
async def user_analytics(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    return await service.user_booking_analytics(skip=skip, limit=limit)


@router.get("/revenue", response_model=RevenueAnalytics)
async def revenue_analytics(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
) -> dict:
    return await service.revenue_analytics(
        start_date=start_date,
        end_date=end_date,
    )
