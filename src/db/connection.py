from pymongo import MongoClient
from pymongo.database import Database

from src.config import settings

_client: MongoClient | None = None
_db: Database | None = None


def connect_to_mongo() -> None:
    global _client
    global _db

    if _client is not None:
        return

    _client = MongoClient(settings.MONGO_URI)
    _db = _client[settings.MONGO_DB]


def close_mongo_connection() -> None:
    global _client
    global _db

    if _client is None:
        return

    _client.close()
    _client = None
    _db = None


def get_database() -> Database:
    if _db is None:
        raise RuntimeError("Database connection is not initialized")

    return _db
