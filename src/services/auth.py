from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

from src.config import settings
from src.mappers.users import user_document_to_public
from src.repositories.users import UserRepository, get_user_repository
from src.schemas.users import UserLogin, UserRegister


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    async def register_user(self, payload: UserRegister) -> dict:
        password_hash = self._hash_password(payload.password)
        doc = {
            "_id": ObjectId(),
            "name": payload.name,
            "email": payload.email.lower(),
            "role": payload.role,
            "password_hash": password_hash,
            "bookings": [],
        }
        try:
            await self._repository.insert_user(doc)
        except DuplicateKeyError as exc:
            raise ValueError("Email already registered") from exc
        return user_document_to_public(doc)

    async def login(self, payload: UserLogin) -> str:
        user_doc = await self._repository.get_user_by_email(payload.email.lower())
        if user_doc is None or not self._verify_password(payload.password, user_doc["password_hash"]):
            raise ValueError("Invalid credentials")

        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=settings.JWT_EXP_MINUTES)
        token = jwt.encode(
            {"sub": str(user_doc["_id"]), "role": user_doc["role"], "exp": exp},
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALG,
        )
        return token


async def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(repository)
