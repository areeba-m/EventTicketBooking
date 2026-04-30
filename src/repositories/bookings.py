from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection

from src.db.async_collections import (
    async_bookings_collection,
    async_events_collection,
    async_users_collection,
)
from src.schemas.bookings import BookingStatus


class BookingRepository:
    def __init__(
        self,
        bookings_collection: AsyncCollection,
        events_collection: AsyncCollection,
        users_collection: AsyncCollection,
    ) -> None:
        self._bookings = bookings_collection
        self._events = events_collection
        self._users = users_collection

    async def get_user(self, user_object_id: ObjectId) -> dict[str, Any] | None:
        return await self._users.find_one({"_id": user_object_id})

    async def get_event(self, event_object_id: ObjectId) -> dict[str, Any] | None:
        return await self._events.find_one({"_id": event_object_id})

    async def get_booking(
        self,
        *,
        booking_object_id: ObjectId,
        user_object_id: ObjectId,
    ) -> dict[str, Any] | None:
        return await self._bookings.find_one(
            {"_id": booking_object_id, "user_id": user_object_id}
        )

    async def list_users_by_status(self, status: str) -> list[dict[str, Any]]:
        pipeline: list[dict[str, Any]] = [
            {"$unwind": "$bookings"},
            {"$match": {"bookings.status": status}},
            {
                "$group": {
                    "_id": "$_id",
                    "name": {"$first": "$name"},
                    "email": {"$first": "$email"},
                    "status": {"$first": "$bookings.status"},
                }
            },
        ]

        cursor = self._users.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def set_event_available_seats(
        self,
        *,
        event_object_id: ObjectId,
        available_seats: int,
    ) -> None:
        await self._events.update_one(
            {"_id": event_object_id, "available_seats": {"$exists": False}},
            {"$set": {"available_seats": available_seats}},
        )

    async def reserve_event_seats(
        self,
        *,
        event_object_id: ObjectId,
        seats: int,
    ) -> dict[str, Any] | None:
        return await self._events.find_one_and_update(
            {"_id": event_object_id, "available_seats": {"$gte": seats}},
            {"$inc": {"available_seats": -seats}},
            return_document=ReturnDocument.AFTER,
        )

    async def release_event_seats(
        self,
        *,
        event_object_id: ObjectId,
        seats: int,
    ) -> None:
        await self._events.update_one(
            {"_id": event_object_id},
            {"$inc": {"available_seats": seats}},
        )

    async def insert_booking(self, booking_doc: dict[str, Any]) -> None:
        await self._bookings.insert_one(booking_doc)

    async def list_bookings_for_user(self, *, user_object_id: ObjectId) -> list[dict[str, Any]]:
        cursor = self._bookings.find({"user_id": user_object_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def mark_booking_cancelled(
        self,
        *,
        booking_object_id: ObjectId,
        user_object_id: ObjectId,
    ) -> dict[str, Any] | None:
        return await self._bookings.find_one_and_update(
            {
                "_id": booking_object_id,
                "user_id": user_object_id,
                "status": BookingStatus.CONFIRMED,
            },
            {"$set": {"status": BookingStatus.CANCELLED}},
            return_document=ReturnDocument.AFTER,
        )

    async def append_user_booking_summary(
        self,
        *,
        user_object_id: ObjectId,
        booking_summary: dict[str, Any],
    ) -> None:
        await self._users.update_one(
            {"_id": user_object_id},
            {"$push": {"bookings": booking_summary}},
        )

    async def append_event_booking_summary(
        self,
        *,
        event_object_id: ObjectId,
        booking_summary: dict[str, Any],
    ) -> None:
        await self._events.update_one(
            {"_id": event_object_id},
            {"$push": {"bookings": booking_summary}},
        )

    async def set_user_booking_status(
        self,
        *,
        user_object_id: ObjectId,
        booking_object_id: ObjectId,
        status: BookingStatus,
    ) -> None:
        await self._users.update_one(
            {"_id": user_object_id},
            {"$set": {"bookings.$[item].status": status}},
            array_filters=[{"item.booking_id": str(booking_object_id)}],
        )

    async def set_event_booking_status(
        self,
        *,
        event_object_id: ObjectId,
        booking_object_id: ObjectId,
        status: BookingStatus,
    ) -> None:
        await self._events.update_one(
            {"_id": event_object_id},
            {"$set": {"bookings.$[item].status": status}},
            array_filters=[{"item.booking_id": str(booking_object_id)}],
        )


async def get_booking_repository() -> BookingRepository:
    return BookingRepository(
        async_bookings_collection(),
        async_events_collection(),
        async_users_collection(),
    )
