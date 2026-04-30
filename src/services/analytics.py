from datetime import datetime
from typing import Any

from fastapi import Depends

from src.mappers.analytics import (
    event_booking_documents_to_public,
    revenue_document_to_public,
    user_booking_documents_to_public,
)
from src.repositories.analytics import AnalyticsRepository, get_analytics_repository


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository) -> None:
        self._repository = repository

    async def event_booking_analytics(
        self,
        *,
        start_date: datetime | None,
        end_date: datetime | None,
        venue: str | None,
        skip: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        match_stage: dict[str, Any] = {"status": "confirmed"}
        pipeline: list[dict[str, Any]] = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$event_id",
                    "total_bookings": {"$sum": 1},
                    "total_tickets": {"$sum": "$seats"},
                }
            },
            {
                "$lookup": {
                    "from": "events",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "event",
                }
            },
            {"$unwind": "$event"},
        ]

        event_match: dict[str, Any] = {}
        if start_date or end_date:
            date_query: dict[str, Any] = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            event_match["event.date"] = date_query
        if venue:
            event_match["event.venue"] = venue
        if event_match:
            pipeline.append({"$match": event_match})

        pipeline.extend(
            [
                {
                    "$project": {
                        "event_id": {"$toString": "$_id"},
                        "title": "$event.title",
                        "date": "$event.date",
                        "venue": "$event.venue",
                        "total_bookings": 1,
                        "total_tickets": 1,
                    }
                },
                {"$skip": skip},
                {"$limit": limit},
            ]
        )

        docs = await self._repository.aggregate_bookings(pipeline)
        return event_booking_documents_to_public(docs)

    async def user_booking_analytics(self, *, skip: int, limit: int) -> list[dict[str, Any]]:
        pipeline: list[dict[str, Any]] = [
            {"$match": {"status": "confirmed"}},
            {
                "$group": {
                    "_id": "$user_id",
                    "total_tickets": {"$sum": "$seats"},
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "user",
                }
            },
            {"$unwind": "$user"},
            {
                "$project": {
                    "user_id": {"$toString": "$_id"},
                    "name": "$user.name",
                    "email": "$user.email",
                    "total_tickets": 1,
                }
            },
            {"$skip": skip},
            {"$limit": limit},
        ]

        docs = await self._repository.aggregate_bookings(pipeline)
        return user_booking_documents_to_public(docs)

    async def revenue_analytics(
        self,
        *,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> dict[str, Any]:
        match_stage: dict[str, Any] = {"status": "confirmed"}
        if start_date or end_date:
            date_query: dict[str, Any] = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            match_stage["created_at"] = date_query

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": None,
                    "total_bookings": {"$sum": 1},
                    "total_tickets": {"$sum": "$seats"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_bookings": 1,
                    "total_tickets": 1,
                }
            },
        ]

        docs = await self._repository.aggregate_bookings(pipeline)
        if not docs:
            return revenue_document_to_public({"total_bookings": 0, "total_tickets": 0})
        return revenue_document_to_public(docs[0])


async def get_analytics_service(
    repository: AnalyticsRepository = Depends(get_analytics_repository),
) -> AnalyticsService:
    return AnalyticsService(repository)
