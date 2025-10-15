from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import User, UserRole, Workspace, Facility, Booking, BookingStatus
from .shemas import (
    RegisterRequest,
    LoginRequest,
    UserOut,
    TokenResponse,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceOut,
    BookingCreate,
    BookingOut,
)
from .auth import hash_password, verify_password, create_access_token, get_current_user, require_admin
from datetime import timedelta
from typing import List


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Coworking Booking API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)


# Auth endpoints
@app.post("/auth/register", response_model=UserOut)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.CUSTOMER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)}, expires_delta=timedelta(minutes=60))
    return TokenResponse(access_token=token)


@app.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# Facilities seed/list (simple helper)
@app.get("/facilities", response_model=List[str])
def list_facilities(db: Session = Depends(get_db)):
    return [f.name for f in db.query(Facility).order_by(Facility.name).all()]


# Workspaces CRUD
@app.get("/workspaces", response_model=List[WorkspaceOut])
def get_workspaces(db: Session = Depends(get_db)):
    items = db.query(Workspace).all()
    return items


@app.get("/workspaces/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(workspace_id: int, db: Session = Depends(get_db)):
    item = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return item


@app.post("/workspaces", response_model=WorkspaceOut)
def create_workspace(
    payload: WorkspaceCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    workspace = Workspace(
        admin_id=admin.id,
        name=payload.name,
        address=payload.address,
        description=payload.description,
        price_per_hour=payload.price_per_hour,
        capacity=payload.capacity,
    )
    if payload.facility_ids:
        facilities = db.query(Facility).filter(Facility.id.in_(payload.facility_ids)).all()
        workspace.facilities = facilities
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


@app.put("/workspaces/{workspace_id}", response_model=WorkspaceOut)
def update_workspace(
    workspace_id: int,
    payload: WorkspaceUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.admin_id != admin.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this workspace")

    for field in ["name", "address", "description", "price_per_hour", "capacity"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(workspace, field, value)

    if payload.facility_ids is not None:
        facilities = db.query(Facility).filter(Facility.id.in_(payload.facility_ids)).all()
        workspace.facilities = facilities

    db.commit()
    db.refresh(workspace)
    return workspace


# Bookings
@app.post("/bookings", response_model=BookingOut)
def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = db.query(Workspace).filter(Workspace.id == payload.workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Conflict check: overlap when (startA < endB) and (endA > startB)
    overlap = (
        db.query(Booking)
        .filter(
            Booking.workspace_id == payload.workspace_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.start_time < payload.end_time,
            Booking.end_time > payload.start_time,
        )
        .first()
    )
    if overlap:
        raise HTTPException(status_code=400, detail="Time slot not available")

    duration_hours = (payload.end_time - payload.start_time).total_seconds() / 3600.0
    if duration_hours <= 0:
        raise HTTPException(status_code=400, detail="Invalid time range")

    total_price = round(duration_hours * ws.price_per_hour, 2)

    booking = Booking(
        user_id=current_user.id,
        workspace_id=payload.workspace_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        total_price=total_price,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@app.get("/bookings/my-bookings", response_model=List[BookingOut])
def my_bookings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Booking)
        .filter(Booking.user_id == current_user.id)
        .order_by(Booking.start_time.desc())
        .all()
    )


@app.get("/workspaces/{workspace_id}/bookings", response_model=List[BookingOut])
def workspace_bookings(
    workspace_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if ws.admin_id != admin.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this workspace")
    return db.query(Booking).filter(Booking.workspace_id == workspace_id).all()


