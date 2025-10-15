from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from .models import UserRole, BookingStatus


# Auth
class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Facilities
class FacilityOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# Workspaces
class WorkspaceBase(BaseModel):
    name: str
    address: str
    description: Optional[str] = None
    price_per_hour: float
    capacity: int
    facility_ids: Optional[List[int]] = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    price_per_hour: Optional[float] = None
    capacity: Optional[int] = None
    facility_ids: Optional[List[int]] = None


class WorkspaceOut(BaseModel):
    id: int
    admin_id: int
    name: str
    address: str
    description: Optional[str]
    price_per_hour: float
    capacity: int
    facilities: List[FacilityOut] = []

    class Config:
        from_attributes = True


# Bookings
class BookingCreate(BaseModel):
    workspace_id: int
    start_time: datetime
    end_time: datetime


class BookingOut(BaseModel):
    id: int
    user_id: int
    workspace_id: int
    start_time: datetime
    end_time: datetime
    total_price: float
    status: BookingStatus

    class Config:
        from_attributes = True


