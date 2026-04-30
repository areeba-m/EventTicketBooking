from __future__ import annotations

from typing import Any

from src.db.utils import serialize_id


def booking_document_to_public(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": serialize_id(doc["_id"]),
        "user_id": serialize_id(doc["user_id"]),
        "event_id": serialize_id(doc["event_id"]),
        "seats": doc["seats"],
        "status": doc["status"],
        "created_at": doc["created_at"],
    }


def booking_documents_to_public(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [booking_document_to_public(doc) for doc in docs]


def booking_status_documents_to_public(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": serialize_id(doc["_id"]),
            "name": doc["name"],
            "email": doc["email"],
            "status": doc["status"],
        }
        for doc in docs
    ]


def booking_summary_document(booking_doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "booking_id": serialize_id(booking_doc["_id"]),
        "event_id": serialize_id(booking_doc["event_id"]),
        "seats": booking_doc["seats"],
        "status": booking_doc["status"],
    }
