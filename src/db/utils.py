from bson import ObjectId
from bson.errors import InvalidId

from src.exceptions import InvalidObjectIdError


def parse_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId as exc:
        raise InvalidObjectIdError("Invalid id") from exc


def serialize_id(value: object) -> str:
    return str(value)
