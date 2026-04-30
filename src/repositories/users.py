from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection

from src.db.async_collections import async_users_collection


class UserRepository:
    def __init__(self, users_collection: AsyncCollection) -> None:
        self._users = users_collection

    async def insert_user(self, user_doc: dict[str, Any]) -> None:
        await self._users.insert_one(user_doc)

    async def get_user_by_id(self, user_object_id: ObjectId) -> dict[str, Any] | None:
        return await self._users.find_one({"_id": user_object_id})

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        return await self._users.find_one({"email": email})


async def get_user_repository() -> UserRepository:
    return UserRepository(async_users_collection())
