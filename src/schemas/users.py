from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field

from src.schemas.bookings import BookingSummary


class UserRole(StrEnum):
    ATTENDEE = "attendee"
    ORGANIZER = "organizer"


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    bookings: list[BookingSummary] = Field(default_factory=list)
