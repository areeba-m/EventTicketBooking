from __future__ import annotations

from typing import Any

from src.db.utils import serialize_id


def _event_booked_seats(event_doc: dict[str, Any]) -> int:
    return sum(item["seats"] for item in event_doc.get("bookings", []))


def event_document_to_public(doc: dict[str, Any]) -> dict[str, Any]:
    available_seats = doc.get("available_seats")
    if available_seats is None:
        available_seats = doc["total_seats"] - _event_booked_seats(doc)
    return {
        "id": serialize_id(doc["_id"]),
        "title": doc["title"],
        "date": doc["date"],
        "venue": doc["venue"],
        "total_seats": doc["total_seats"],
        "available_seats": available_seats,
        "bookings": doc.get("bookings", []),
    }


def event_documents_to_public(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event_document_to_public(doc) for doc in docs]
