from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Float,
    Enum as SqlEnum,
    UniqueConstraint,
    Table,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .database import Base


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"


workspace_facilities = Table(
    "workspace_facilities",
    Base.metadata,
    Column("workspace_id", ForeignKey("workspaces.id"), primary_key=True),
    Column("facility_id", ForeignKey("facilities.id"), primary_key=True),
    UniqueConstraint("workspace_id", "facility_id", name="uq_workspace_facility"),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)

    workspaces: Mapped[list["Workspace"]] = relationship("Workspace", back_populates="admin", cascade="all, delete")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="user", cascade="all, delete")


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price_per_hour: Mapped[float] = mapped_column(Float, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    admin: Mapped[User] = relationship("User", back_populates="workspaces")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="workspace", cascade="all, delete")
    facilities: Mapped[list["Facility"]] = relationship(
        "Facility", secondary=workspace_facilities, back_populates="workspaces"
    )


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    workspaces: Mapped[list[Workspace]] = relationship(
        "Workspace", secondary=workspace_facilities, back_populates="facilities"
    )


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(SqlEnum(BookingStatus), nullable=False, default=BookingStatus.PENDING)

    user: Mapped[User] = relationship("User", back_populates="bookings")
    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="bookings")


