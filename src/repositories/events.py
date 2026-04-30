from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection

from src.db.async_collections import async_events_collection


class EventRepository:
    def __init__(self, events_collection: AsyncCollection) -> None:
        self._events = events_collection

    async def insert_event(self, event_doc: dict[str, Any]) -> None:
        await self._events.insert_one(event_doc)

    async def find_events(
        self,
        *,
        query: dict[str, Any],
        skip: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        cursor = self._events.find(query).skip(skip).limit(limit)
        return await cursor.to_list(length=None)

    async def get_event(self, event_object_id: ObjectId) -> dict[str, Any] | None:
        return await self._events.find_one({"_id": event_object_id})

    async def update_event(self, *, event_object_id: ObjectId, updates: dict[str, Any]) -> None:
        await self._events.update_one({"_id": event_object_id}, {"$set": updates})

    async def delete_event(self, event_object_id: ObjectId) -> bool:
        result = await self._events.delete_one({"_id": event_object_id})
        return result.deleted_count > 0


async def get_event_repository() -> EventRepository:
    return EventRepository(async_events_collection())
