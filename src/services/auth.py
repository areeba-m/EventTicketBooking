from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from pymongo.errors import DuplicateKeyError

from src.config import settings
from src.schemas.users import UserLogin, UserRegister
from src.services import users as user_service


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def register_user(payload: UserRegister) -> dict:
    password_hash = _hash_password(payload.password)
    try:
        return user_service.create_user(payload, password_hash)
    except DuplicateKeyError as exc:
        raise ValueError("Email already registered") from exc


def login(payload: UserLogin) -> str:
    user_doc = user_service.get_user_by_email(payload.email)
    if user_doc is None or not _verify_password(payload.password, user_doc["password_hash"]):
        raise ValueError("Invalid credentials")

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.JWT_EXP_MINUTES)
    token = jwt.encode(
        {"sub": str(user_doc["_id"]), "role": user_doc["role"], "exp": exp},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )
    return token
