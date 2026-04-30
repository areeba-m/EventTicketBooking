from __future__ import annotations

import inspect

from pymongo.asynchronous.mongo_client import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from src.config import settings

_async_client: AsyncMongoClient | None = None
_async_db: AsyncDatabase | None = None


def get_async_database() -> AsyncDatabase:
    if _async_db is None:
        raise RuntimeError("Async database connection is not initialized")
    return _async_db


async def connect_to_mongo_async() -> None:
    global _async_client
    global _async_db

    if _async_client is not None:
        return

    _async_client = AsyncMongoClient(settings.MONGO_URI)
    _async_db = _async_client[settings.MONGO_DB]


async def close_mongo_connection_async() -> None:
    global _async_client
    global _async_db

    if _async_client is None:
        return

    close_result = _async_client.close()
    if inspect.isawaitable(close_result):
        await close_result

    _async_client = None
    _async_db = None
