import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pymongo.collection import Collection

from src.db.collections import bookings_collection, events_collection, users_collection
from src.dependencies.auth import require_role
from src.schemas.bookings import BookingCreate, BookingPublic
from src.schemas.users import UserRole
from src.services import background_tasks as bg_tasks, bookings as booking_service

logger = logging.getLogger("event_ticket_booking")
router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingPublic, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    current_user: Annotated[dict, Depends(require_role(UserRole.ATTENDEE))],
    bookings: Annotated[Collection, Depends(bookings_collection)],
    events: Annotated[Collection, Depends(events_collection)],
    users: Annotated[Collection, Depends(users_collection)],
    bg: BackgroundTasks,
) -> dict:
    try:
        booking = booking_service.create_booking(
            bookings,
            events,
            users,
            user_id=current_user["id"],
            payload=payload,
        )
        logger.info(
            "Booking created: id=%s, user=%s, event=%s, seats=%d",
            booking["id"],
            current_user["id"],
            booking["event_id"],
            booking["seats"],
        )
        bg.add_task(
            bg_tasks.send_booking_confirmation,
            booking["id"],
            current_user["id"],
            booking["event_id"],
            booking["seats"],
        )
        return booking
    except ValueError as exc:
        logger.warning("Booking creation failed for user %s: %s", current_user["id"], str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/me", response_model=list[BookingPublic])
def list_my_bookings(
    current_user: Annotated[dict, Depends(require_role(UserRole.ATTENDEE))],
    bookings: Annotated[Collection, Depends(bookings_collection)],
) -> list[dict]:
    try:
        return booking_service.list_bookings_for_user(bookings, user_id=current_user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{booking_id}", response_model=BookingPublic)
def cancel_booking(
    booking_id: str,
    current_user: Annotated[dict, Depends(require_role(UserRole.ATTENDEE))],
    bookings: Annotated[Collection, Depends(bookings_collection)],
    events: Annotated[Collection, Depends(events_collection)],
    users: Annotated[Collection, Depends(users_collection)],
    bg: BackgroundTasks,
) -> dict:
    try:
        booking = booking_service.cancel_booking(
            bookings,
            events,
            users,
            user_id=current_user["id"],
            booking_id=booking_id,
        )
    except ValueError as exc:
        logger.warning("Booking cancellation failed for user %s: %s", current_user["id"], str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    logger.info(
        "Booking cancelled: id=%s, user=%s, seats_restored=%d",
        booking["id"],
        current_user["id"],
        booking["seats"],
    )
    bg.add_task(bg_tasks.send_booking_cancellation, booking["id"], current_user["id"], booking["seats"])
    return booking
