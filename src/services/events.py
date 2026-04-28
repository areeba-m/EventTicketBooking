from datetime import datetime
from typing import Any

from src.db.collections import events_collection
from src.db.utils import parse_object_id, serialize_id
from src.schemas.events import EventCreate, EventUpdate


def _available_seats(doc: dict[str, Any]) -> int:
    booked = sum(item["seats"] for item in doc.get("bookings", []))
    return doc["total_seats"] - booked


def _booked_seats(doc: dict[str, Any]) -> int:
    return sum(item["seats"] for item in doc.get("bookings", []))


def _serialize_event(doc: dict[str, Any]) -> dict[str, Any]:
    available_seats = doc.get("available_seats")
    if available_seats is None:
        available_seats = _available_seats(doc)
    return {
        "id": serialize_id(doc["_id"]),
        "title": doc["title"],
        "date": doc["date"],
        "venue": doc["venue"],
        "total_seats": doc["total_seats"],
        "available_seats": available_seats,
        "bookings": doc.get("bookings", []),
    }


def create_event(payload: EventCreate) -> dict[str, Any]:
    doc = {
        "title": payload.title,
        "date": payload.date,
        "venue": payload.venue,
        "total_seats": payload.total_seats,
        "available_seats": payload.total_seats,
        "bookings": [],
    }
    events_collection().insert_one(doc)
    return _serialize_event(doc)


def list_events(
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

    docs = events_collection().find(query).skip(skip).limit(limit)
    return [_serialize_event(doc) for doc in docs]


def get_event(event_id: str) -> dict[str, Any] | None:
    doc = events_collection().find_one({"_id": parse_object_id(event_id)})
    if doc is None:
        return None
    return _serialize_event(doc)


def update_event(event_id: str, payload: EventUpdate) -> dict[str, Any] | None:
    event_object_id = parse_object_id(event_id)
    event_doc = events_collection().find_one({"_id": event_object_id})
    if event_doc is None:
        return None

    updates = payload.model_dump(exclude_unset=True)
    if "total_seats" in updates:
        available = event_doc.get("available_seats")
        if available is None:
            booked = _booked_seats(event_doc)
        else:
            booked = event_doc["total_seats"] - available
        new_total = updates["total_seats"]
        if new_total is not None and new_total < booked:
            raise ValueError("Total seats cannot be less than already booked seats")
        if new_total is not None:
            updates["available_seats"] = new_total - booked

    if not updates:
        return _serialize_event(event_doc)

    events_collection().update_one({"_id": event_object_id}, {"$set": updates})
    updated = events_collection().find_one({"_id": event_object_id})
    if updated is None:
        return None
    return _serialize_event(updated)


def delete_event(event_id: str) -> bool:
    event_object_id = parse_object_id(event_id)
    result = events_collection().delete_one({"_id": event_object_id})
    return result.deleted_count > 0
