from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.dependencies.auth import require_role
from src.schemas.events import EventCreate, EventPublic, EventUpdate
from src.schemas.users import UserRole
from src.services.events import EventService, get_event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventPublic, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    _: Annotated[dict, Depends(require_role(UserRole.ORGANIZER))],
    service: Annotated[EventService, Depends(get_event_service)],
) -> dict:
    return await service.create_event(payload)


@router.get("", response_model=list[EventPublic])
async def list_events(
    service: Annotated[EventService, Depends(get_event_service)],
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    venue: str | None = Query(default=None, min_length=1, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    return await service.list_events(
        start_date=start_date,
        end_date=end_date,
        venue=venue,
        skip=skip,
        limit=limit,
    )


@router.get("/{event_id}", response_model=EventPublic)
async def get_event(
    event_id: str,
    service: Annotated[EventService, Depends(get_event_service)],
) -> dict:
    try:
        event = await service.get_event(event_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=EventPublic)
async def update_event(
    event_id: str,
    payload: EventUpdate,
    _: Annotated[dict, Depends(require_role(UserRole.ORGANIZER))],
    service: Annotated[EventService, Depends(get_event_service)],
) -> dict:
    try:
        event = await service.update_event(event_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    _: Annotated[dict, Depends(require_role(UserRole.ORGANIZER))],
    service: Annotated[EventService, Depends(get_event_service)],
) -> None:
    try:
        deleted = await service.delete_event(event_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return None
