from typing import Any

from bson import ObjectId
from fastapi import Depends

from src.db.utils import parse_object_id
from src.mappers.users import user_document_to_public
from src.repositories.users import UserRepository, get_user_repository
from src.schemas.users import UserRegister


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def create_user(self, payload: UserRegister, password_hash: str) -> dict[str, Any]:
        doc = {
            "_id": ObjectId(),
            "name": payload.name,
            "email": payload.email.lower(),
            "role": payload.role,
            "password_hash": password_hash,
            "bookings": [],
        }
        await self._repository.insert_user(doc)
        return user_document_to_public(doc)

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        doc = await self._repository.get_user_by_id(parse_object_id(user_id))
        if doc is None:
            return None
        return user_document_to_public(doc)


async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)
