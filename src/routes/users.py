from typing import Annotated

from fastapi import APIRouter, Depends

from src.dependencies.auth import get_current_user
from src.schemas.users import UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def get_me(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    return current_user
