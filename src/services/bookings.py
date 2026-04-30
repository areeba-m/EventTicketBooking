from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import Depends

from src.db.utils import parse_object_id
from src.mappers.bookings import (
    booking_document_to_public,
    booking_documents_to_public,
    booking_status_documents_to_public,
    booking_summary_document,
)
from src.repositories.bookings import BookingRepository, get_booking_repository
from src.schemas.bookings import BookingCreate, BookingStatus


class BookingService:
    def __init__(self, repository: BookingRepository) -> None:
        self._repository = repository

    @staticmethod
    def _event_booked_seats(event_doc: dict[str, Any]) -> int:
        return sum(item["seats"] for item in event_doc.get("bookings", []))

    async def list_users_by_status(self, status: str) -> list[dict[str, Any]]:
        normalized_status = status.strip().lower()
        allowed_status = {BookingStatus.CONFIRMED.value, BookingStatus.CANCELLED.value}
        if normalized_status not in allowed_status:
            raise ValueError("Invalid booking status")

        docs = await self._repository.list_users_by_status(normalized_status)
        return booking_status_documents_to_public(docs)

    async def create_booking(self, *, user_id: str, payload: BookingCreate) -> dict[str, Any]:
        user_object_id = parse_object_id(user_id)
        event_object_id = parse_object_id(payload.event_id)

        user_doc = await self._repository.get_user(user_object_id)
        if user_doc is None:
            raise ValueError("User not found")

        event_doc = await self._repository.get_event(event_object_id)
        if event_doc is None:
            raise ValueError("Event not found")

        if "available_seats" not in event_doc:
            available_seats = event_doc["total_seats"] - self._event_booked_seats(event_doc)
            await self._repository.set_event_available_seats(
                event_object_id=event_object_id,
                available_seats=available_seats,
            )

        updated_event = await self._repository.reserve_event_seats(
            event_object_id=event_object_id,
            seats=payload.seats,
        )
        if updated_event is None:
            raise ValueError("Not enough seats available")

        booking_doc = {
            "_id": ObjectId(),
            "user_id": user_object_id,
            "event_id": event_object_id,
            "seats": payload.seats,
            "status": BookingStatus.CONFIRMED,
            "created_at": datetime.now(timezone.utc),
        }
        try:
            await self._repository.insert_booking(booking_doc)
        except Exception:
            await self._repository.release_event_seats(
                event_object_id=event_object_id,
                seats=payload.seats,
            )
            raise

        summary = booking_summary_document(booking_doc)
        await self._repository.append_user_booking_summary(
            user_object_id=user_object_id,
            booking_summary=summary,
        )
        await self._repository.append_event_booking_summary(
            event_object_id=event_object_id,
            booking_summary=summary,
        )

        return booking_document_to_public(booking_doc)

    async def list_bookings_for_user(self, *, user_id: str) -> list[dict[str, Any]]:
        user_object_id = parse_object_id(user_id)
        docs = await self._repository.list_bookings_for_user(user_object_id=user_object_id)
        return booking_documents_to_public(docs)

    async def cancel_booking(self, *, user_id: str, booking_id: str) -> dict[str, Any] | None:
        user_object_id = parse_object_id(user_id)
        booking_object_id = parse_object_id(booking_id)

        booking_doc = await self._repository.get_booking(
            booking_object_id=booking_object_id,
            user_object_id=user_object_id,
        )
        if booking_doc is None:
            return None
        if booking_doc["status"] == BookingStatus.CANCELLED:
            return booking_document_to_public(booking_doc)

        updated_booking = await self._repository.mark_booking_cancelled(
            booking_object_id=booking_object_id,
            user_object_id=user_object_id,
        )
        if updated_booking is None:
            return booking_document_to_public(booking_doc)

        await self._repository.release_event_seats(
            event_object_id=booking_doc["event_id"],
            seats=booking_doc["seats"],
        )
        await self._repository.set_user_booking_status(
            user_object_id=user_object_id,
            booking_object_id=booking_object_id,
            status=BookingStatus.CANCELLED,
        )
        await self._repository.set_event_booking_status(
            event_object_id=booking_doc["event_id"],
            booking_object_id=booking_object_id,
            status=BookingStatus.CANCELLED,
        )

        return booking_document_to_public(updated_booking)


async def get_booking_service(
    repository: BookingRepository = Depends(get_booking_repository),
) -> BookingService:
    return BookingService(repository)
