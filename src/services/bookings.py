from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.collection import Collection

from src.db.utils import parse_object_id, serialize_id
from src.schemas.bookings import BookingCreate, BookingStatus

from src.db.connection import get_database


def _serialize_booking(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": serialize_id(doc["_id"]),
        "user_id": serialize_id(doc["user_id"]),
        "event_id": serialize_id(doc["event_id"]),
        "seats": doc["seats"],
        "status": doc["status"],
        "created_at": doc["created_at"],
    }


def _event_booked_seats(event_doc: dict[str, Any]) -> int:
    return sum(item["seats"] for item in event_doc.get("bookings", []))


def _validate_user_and_event(
    users_collection: Collection,
    events_collection: Collection,
    *,
    user_object_id: ObjectId,
    event_object_id: ObjectId,
) -> dict[str, Any]:
    user_doc = get_database()["users"].find_one({"_id": user_object_id})
    if user_doc is None:
        raise ValueError("User not found")

    event_doc = events_collection.find_one({"_id": event_object_id})
    if event_doc is None:
        raise ValueError("Event not found")

    return event_doc


def _reserve_seats(
    events_collection: Collection,
    *,
    event_object_id: ObjectId,
    seats: int,
) -> dict[str, Any]:
    updated_event = events_collection.find_one_and_update(
        {"_id": event_object_id, "available_seats": {"$gte": seats}},
        {"$inc": {"available_seats": -seats}},
        return_document=ReturnDocument.AFTER,
    )
    if updated_event is None:
        raise ValueError("Not enough seats available")
    return updated_event


def create_booking(
    bookings_collection: Collection,
    events_collection: Collection,
    users_collection: Collection,
    *,
    user_id: str,
    payload: BookingCreate,
) -> dict[str, Any]:
    user_object_id = parse_object_id(user_id)
    event_object_id = parse_object_id(payload.event_id)

    event_doc = _validate_user_and_event(
        users_collection,
        events_collection,
        user_object_id=user_object_id,
        event_object_id=event_object_id,
    )

    if "available_seats" not in event_doc:
        available = event_doc["total_seats"] - _event_booked_seats(event_doc)
        events_collection.update_one(
            {"_id": event_object_id, "available_seats": {"$exists": False}},
            {"$set": {"available_seats": available}},
        )

    _reserve_seats(events_collection, event_object_id=event_object_id, seats=payload.seats)

    booking_id = ObjectId()
    booking_doc = {
        "_id": booking_id,
        "user_id": user_object_id,
        "event_id": event_object_id,
        "seats": payload.seats,
        "status": BookingStatus.CONFIRMED,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        bookings_collection.insert_one(booking_doc)
    except Exception:
        events_collection.update_one({"_id": event_object_id}, {"$inc": {"available_seats": payload.seats}})
        raise

    summary = {
        "booking_id": serialize_id(booking_id),
        "event_id": serialize_id(event_object_id),
        "seats": payload.seats,
        "status": BookingStatus.CONFIRMED,
    }

    # Embed booking summaries for quick reads while keeping bookings normalized.
    users_collection.update_one({"_id": user_object_id}, {"$push": {"bookings": summary}})
    events_collection.update_one({"_id": event_object_id}, {"$push": {"bookings": summary}})

    return _serialize_booking(booking_doc)


def list_bookings_for_user(
    bookings_collection: Collection,
    *,
    user_id: str,
) -> list[dict[str, Any]]:
    user_object_id = parse_object_id(user_id)
    docs = bookings_collection.find({"user_id": user_object_id}).sort("created_at", -1)
    return [_serialize_booking(doc) for doc in docs]


def cancel_booking(
    bookings_collection: Collection,
    events_collection: Collection,
    users_collection: Collection,
    *,
    user_id: str,
    booking_id: str,
) -> dict[str, Any] | None:
    user_object_id = parse_object_id(user_id)
    booking_object_id = parse_object_id(booking_id)

    booking_doc = bookings_collection.find_one({"_id": booking_object_id, "user_id": user_object_id})
    if booking_doc is None:
        return None
    if booking_doc["status"] == BookingStatus.CANCELLED:
        return _serialize_booking(booking_doc)

    updated_booking = bookings_collection.find_one_and_update(
        {"_id": booking_object_id, "user_id": user_object_id, "status": BookingStatus.CONFIRMED},
        {"$set": {"status": BookingStatus.CANCELLED}},
        return_document=ReturnDocument.AFTER,
    )
    if updated_booking is None:
        return _serialize_booking(booking_doc)

    events_collection.update_one(
        {"_id": booking_doc["event_id"]},
        {"$inc": {"available_seats": booking_doc["seats"]}},
    )

    users_collection.update_one(
        {"_id": user_object_id},
        {"$set": {"bookings.$[item].status": BookingStatus.CANCELLED}},
        array_filters=[{"item.booking_id": serialize_id(booking_object_id)}],
    )
    events_collection.update_one(
        {"_id": booking_doc["event_id"]},
        {"$set": {"bookings.$[item].status": BookingStatus.CANCELLED}},
        array_filters=[{"item.booking_id": serialize_id(booking_object_id)}],
    )

    return _serialize_booking(updated_booking)
