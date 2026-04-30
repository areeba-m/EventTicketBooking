from datetime import datetime
from typing import Any

from fastapi import Depends

from src.db.utils import parse_object_id
from src.mappers.events import event_document_to_public, event_documents_to_public
from src.repositories.events import EventRepository, get_event_repository
from src.schemas.events import EventCreate, EventUpdate


class EventService:
    def __init__(self, repository: EventRepository) -> None:
        self._repository = repository

    @staticmethod
    def _event_booked_seats(doc: dict[str, Any]) -> int:
        return sum(item["seats"] for item in doc.get("bookings", []))

    async def create_event(self, payload: EventCreate) -> dict[str, Any]:
        doc = {
            "title": payload.title,
            "date": payload.date,
            "venue": payload.venue,
            "total_seats": payload.total_seats,
            "available_seats": payload.total_seats,
            "bookings": [],
        }
        await self._repository.insert_event(doc)
        return event_document_to_public(doc)

    async def list_events(
        self,
        *,
        start_date: datetime | None,
        end_date: datetime | None,
        venue: str | None,
        skip: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if start_date or end_date:
            date_query: dict[str, Any] = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["date"] = date_query
        if venue:
            query["venue"] = venue

        docs = await self._repository.find_events(query=query, skip=skip, limit=limit)
        return event_documents_to_public(docs)

    async def get_event(self, event_id: str) -> dict[str, Any] | None:
        doc = await self._repository.get_event(parse_object_id(event_id))
        if doc is None:
            return None
        return event_document_to_public(doc)

    async def update_event(self, event_id: str, payload: EventUpdate) -> dict[str, Any] | None:
        event_object_id = parse_object_id(event_id)
        event_doc = await self._repository.get_event(event_object_id)
        if event_doc is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        if "total_seats" in updates:
            available = event_doc.get("available_seats")
            if available is None:
                booked = self._event_booked_seats(event_doc)
            else:
                booked = event_doc["total_seats"] - available
            new_total = updates["total_seats"]
            if new_total is not None and new_total < booked:
                raise ValueError("Total seats cannot be less than already booked seats")
            if new_total is not None:
                updates["available_seats"] = new_total - booked

        if not updates:
            return event_document_to_public(event_doc)

        await self._repository.update_event(event_object_id=event_object_id, updates=updates)
        updated = await self._repository.get_event(event_object_id)
        if updated is None:
            return None
        return event_document_to_public(updated)

    async def delete_event(self, event_id: str) -> bool:
        event_object_id = parse_object_id(event_id)
        return await self._repository.delete_event(event_object_id)


async def get_event_service(
    repository: EventRepository = Depends(get_event_repository),
) -> EventService:
    return EventService(repository)
