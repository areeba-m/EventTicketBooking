from __future__ import annotations

from typing import Any

from src.db.utils import serialize_id


def user_document_to_public(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": serialize_id(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "role": doc["role"],
        "bookings": doc.get("bookings", []),
    }
