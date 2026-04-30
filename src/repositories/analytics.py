from __future__ import annotations

from typing import Any

from pymongo.asynchronous.collection import AsyncCollection

from src.db.async_collections import async_analytics_bookings_collection


class AnalyticsRepository:
    def __init__(self, bookings_collection: AsyncCollection) -> None:
        self._bookings = bookings_collection

    async def aggregate_bookings(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cursor = self._bookings.aggregate(pipeline)
        return await cursor.to_list(length=None)


async def get_analytics_repository() -> AnalyticsRepository:
    return AnalyticsRepository(async_analytics_bookings_collection())
