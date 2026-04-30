import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status as http_status
from src.dependencies.auth import require_role
from src.schemas.bookings import BookingCreate, BookingPublic
from src.schemas.users import UserBookingStatusPublic, UserRole
from src.services import background_tasks as bg_tasks
from src.services.bookings import BookingService, get_booking_service


logger = logging.getLogger("event_ticket_booking")
router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingPublic, status_code=http_status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    current_user: Annotated[dict, Depends(require_role(UserRole.ATTENDEE))],
    service: Annotated[BookingService, Depends(get_booking_service)],
    bg: BackgroundTasks,
) -> dict:
    try:
        booking = await service.create_booking(
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
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/me", response_model=list[BookingPublic])
async def list_my_bookings(
    current_user: Annotated[dict, Depends(require_role(UserRole.ATTENDEE))],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> list[dict]:
    try:
        return await service.list_bookings_for_user(user_id=current_user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{status}", response_model=list[UserBookingStatusPublic])
async def list_users_by_status(
    status: str,
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> list[dict]:
    try:
        return await service.list_users_by_status(status)
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

@router.delete("/{booking_id}", response_model=BookingPublic)
async def cancel_booking(
    booking_id: str,
    current_user: Annotated[dict, Depends(require_role(UserRole.ATTENDEE))],
    service: Annotated[BookingService, Depends(get_booking_service)],
    bg: BackgroundTasks,
) -> dict:
    try:
        booking = await service.cancel_booking(user_id=current_user["id"], booking_id=booking_id)
    except ValueError as exc:
        logger.warning("Booking cancellation failed for user %s: %s", current_user["id"], str(exc))
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if booking is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    logger.info(
        "Booking cancelled: id=%s, user=%s, seats_restored=%d",
        booking["id"],
        current_user["id"],
        booking["seats"],
    )
    bg.add_task(bg_tasks.send_booking_cancellation, booking["id"], current_user["id"], booking["seats"])
    return booking
