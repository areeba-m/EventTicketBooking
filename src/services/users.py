from typing import Any

from src.db.collections import users_collection
from src.db.utils import parse_object_id, serialize_id
from src.schemas.users import UserRegister


def _serialize_user(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": serialize_id(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "role": doc["role"],
        "bookings": doc.get("bookings", []),
    }


def create_user(payload: UserRegister, password_hash: str) -> dict[str, Any]:
    doc = {
        "name": payload.name,
        "email": payload.email.lower(),
        "role": payload.role,
        "password_hash": password_hash,
        "bookings": [],
    }
    users_collection().insert_one(doc)
    return _serialize_user(doc)


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    doc = users_collection().find_one({"_id": parse_object_id(user_id)})
    if doc is None:
        return None
    return _serialize_user(doc)


def get_user_by_email(email: str) -> dict[str, Any] | None:
    return users_collection().find_one({"email": email.lower()})
