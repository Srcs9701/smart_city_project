"""
Smart City Parking Management System - FastAPI Backend

Endpoints:
    Parking Lots:   POST, GET, GET/{id}, PUT/{id}, DELETE/{id}
    Parking Spaces: GET (list with filters)
    Sensor Events:  POST /entry, POST /exit, POST /extend, GET /events
    Alerts:         POST, GET, PUT/{id}/resolve
    Analytics:      GET /summary, GET /weekly

Run: python main.py -> opens at http://localhost:8000
"""

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import jwt
import os

from database import init_db, get_db, ParkingLot, ParkingSpace, ParkingEvent, Alert
from simulator import seed_data
from analytics import get_weekly_analytics
from schemas import (
    ParkingLotCreate, ParkingLotUpdate, ParkingLotResponse,
    ParkingSpaceResponse,
    VehicleEntryRequest, VehicleExitRequest, VehicleExtensionRequest, ParkingEventResponse,
    ParkingEventDetailsResponse,
    AlertCreate, AlertResponse,
    DashboardSummary, LotSummary, WeeklyAnalytics
)


# ─── Lifespan: Initialize DB and seed data on startup ────────────
@asynccontextmanager
async def lifespan(app):
    """Runs once when the server starts."""
    init_db()       # Create tables
    seed_data()     # Generate 1 week of simulated data
    yield


# ─── Create FastAPI app ──────────────────────────────────────────
app = FastAPI(
    title="Smart City Parking Management System",
    description="IoT-based parking platform that monitors occupancy and provides analytics",
    version="1.0.0",
    lifespan=lifespan
)


# ─── Authentication Setup ────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
# Updated admin credentials per user request
ADMIN_USERNAME = "helloworld"
ADMIN_PASSWORD = "hw123"


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    message: str


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    per_page: int
    total_pages: int


def verify_token(token: str) -> bool:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub") == ADMIN_USERNAME
    except:
        return False


# ─── Authentication Endpoints ───────────────────────────────────
@app.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
def login(credentials: LoginRequest):
    """Admin login endpoint."""
    if credentials.username == ADMIN_USERNAME and credentials.password == ADMIN_PASSWORD:
        token = jwt.encode(
            {"sub": ADMIN_USERNAME},
            SECRET_KEY,
            algorithm="HS256"
        )
        return {"token": token, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


# ══════════════════════════════════════════════════════════════════
# PARKING LOT ENDPOINTS (CRUD - POST, GET, PUT, DELETE)
# ══════════════════════════════════════════════════════════════════

@app.post("/api/lots", response_model=ParkingLotResponse, tags=["Parking Lots"], status_code=201)
def create_lot(lot: ParkingLotCreate, db: Session = Depends(get_db)):
    """
    Create a new parking lot.
    Automatically generates parking spaces (A1, A2, B1, B2...) based on total_spaces.
    """
    # Create the lot
    db_lot = ParkingLot(
        name=lot.name,
        location=lot.location,
        total_spaces=lot.total_spaces
    )
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)

    # Auto-generate parking spaces
    for i in range(1, lot.total_spaces + 1):
        row = chr(64 + ((i - 1) // 10) + 1)
        num = ((i - 1) % 10) + 1
        space = ParkingSpace(
            lot_id=db_lot.id,
            space_number=f"{row}{num}",
            is_occupied=False
        )
        db.add(space)
    db.commit()

    return db_lot


@app.get("/api/lots", response_model=List[ParkingLotResponse], tags=["Parking Lots"])
def list_lots(db: Session = Depends(get_db)):
    """List all registered parking lots."""
    return db.query(ParkingLot).all()


@app.get("/api/lots/{lot_id}", response_model=ParkingLotResponse, tags=["Parking Lots"])
def get_lot(lot_id: int, db: Session = Depends(get_db)):
    """Get a specific parking lot by ID."""
    lot = db.query(ParkingLot).filter(ParkingLot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")
    return lot


@app.put("/api/lots/{lot_id}", response_model=ParkingLotResponse, tags=["Parking Lots"])
def update_lot(lot_id: int, lot_update: ParkingLotUpdate, db: Session = Depends(get_db)):
    """
    Update an existing parking lot.
    Only provided fields will be updated (partial update).
    """
    lot = db.query(ParkingLot).filter(ParkingLot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")

    # Only update fields that were provided
    update_data = lot_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lot, field, value)

    db.commit()
    db.refresh(lot)
    return lot


@app.delete("/api/lots/{lot_id}", tags=["Parking Lots"])
def delete_lot(lot_id: int, db: Session = Depends(get_db)):
    """Delete a parking lot and all its associated spaces and events."""
    lot = db.query(ParkingLot).filter(ParkingLot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")

    # Delete associated events and spaces first (cascade)
    spaces = db.query(ParkingSpace).filter(ParkingSpace.lot_id == lot_id).all()
    for space in spaces:
        db.query(ParkingEvent).filter(ParkingEvent.space_id == space.id).delete()
        db.query(Alert).filter(Alert.space_id == space.id).delete()
    db.query(ParkingSpace).filter(ParkingSpace.lot_id == lot_id).delete()
    db.delete(lot)
    db.commit()

    return {"message": f"Parking lot '{lot.name}' deleted successfully"}


# ══════════════════════════════════════════════════════════════════
# PARKING SPACE ENDPOINTS (GET with filters)
# ══════════════════════════════════════════════════════════════════

@app.get("/api/spaces", response_model=List[ParkingSpaceResponse], tags=["Parking Spaces"])
def list_spaces(
    lot_id: Optional[int] = Query(None, description="Filter by parking lot ID"),
    status: Optional[str] = Query(None, description="Filter: 'occupied' or 'available'"),
    db: Session = Depends(get_db)
):
    """
    List parking spaces with optional filters.
    - Filter by lot_id to see spaces in a specific lot
    - Filter by status: 'occupied' or 'available'
    """
    query = db.query(ParkingSpace)

    if lot_id:
        query = query.filter(ParkingSpace.lot_id == lot_id)
    if status == "occupied":
        query = query.filter(ParkingSpace.is_occupied == True)
    elif status == "available":
        query = query.filter(ParkingSpace.is_occupied == False)

    return query.all()


# ══════════════════════════════════════════════════════════════════
# SENSOR EVENT ENDPOINTS (IoT Sensor Simulation)
# ══════════════════════════════════════════════════════════════════

@app.post("/api/sensor/entry", response_model=ParkingEventResponse, tags=["Sensor Events"], status_code=201)
def vehicle_entry(data: VehicleEntryRequest, db: Session = Depends(get_db)):
    """
    Record a vehicle entry event (simulates IoT sensor).
    - Marks the parking space as occupied
    - Creates a new parking event record
    - Raises alert if space is already occupied (double parking)
    """
    space = db.query(ParkingSpace).filter(ParkingSpace.id == data.space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Parking space not found")

    # Check for double parking violation
    if space.is_occupied:
        alert = Alert(
            space_id=space.id,
            alert_type="double_parking",
            message=f"Double parking attempt by {data.vehicle_number} at space {space.space_number}"
        )
        db.add(alert)
        db.commit()
        raise HTTPException(status_code=409, detail="Space already occupied - double parking alert created")

    # Mark space as occupied
    space.is_occupied = True

    # Check if this lot's occupancy exceeds 80% threshold
    lot = space.lot
    spaces = db.query(ParkingSpace).filter(ParkingSpace.lot_id == lot.id).all()
    occupied_count = sum(1 for s in spaces if s.is_occupied)
    occupancy_pct = (occupied_count / lot.total_spaces) * 100
    if occupancy_pct >= 80.0:
        alert = Alert(
            space_id=space.id,
            alert_type="high_occupancy",
            message=f"High occupancy alert: {lot.name} is {occupancy_pct:.1f}% full ({occupied_count}/{lot.total_spaces} spaces)"
        )
        db.add(alert)

    # Create parking event
    event = ParkingEvent(
        space_id=data.space_id,
        vehicle_number=data.vehicle_number,
        entry_time=datetime.now(),
        allowed_duration_hours=4.0
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@app.post("/api/sensor/exit", response_model=ParkingEventResponse, tags=["Sensor Events"])
def vehicle_exit(data: VehicleExitRequest, db: Session = Depends(get_db)):
    """
    Record a vehicle exit event (simulates IoT sensor).
    - Marks the parking space as available
    - Updates the parking event with exit time and duration
    - Creates overstay alert if duration > allowed limit
    """
    space = db.query(ParkingSpace).filter(ParkingSpace.id == data.space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Parking space not found")

    # Find the active event for this space
    event = db.query(ParkingEvent).filter(
        ParkingEvent.space_id == data.space_id,
        ParkingEvent.vehicle_number == data.vehicle_number,
        ParkingEvent.exit_time == None
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="No active parking event found for this vehicle")

    # Mark space as available
    space.is_occupied = False

    # Update event with exit time and duration
    event.exit_time = datetime.now()
    event.duration_hours = round((event.exit_time - event.entry_time).total_seconds() / 3600, 2)

    # Check for overstay violation (> allowed duration)
    if event.duration_hours > event.allowed_duration_hours:
        alert = Alert(
            space_id=space.id,
            alert_type="overstay",
            message=f"Vehicle {data.vehicle_number} overstayed for {event.duration_hours} hours (allowed: {event.allowed_duration_hours} hours) at space {space.space_number}"
        )
        db.add(alert)

    db.commit()
    db.refresh(event)
    return event


@app.post("/api/sensor/extend", response_model=ParkingEventResponse, tags=["Sensor Events"])
def extend_parking_time(data: VehicleExtensionRequest, db: Session = Depends(get_db)):
    """
    Extend the allowed parking duration for a vehicle.
    """
    space = db.query(ParkingSpace).filter(ParkingSpace.id == data.space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Parking space not found")

    # Find active event
    event = db.query(ParkingEvent).filter(
        ParkingEvent.space_id == data.space_id,
        ParkingEvent.vehicle_number == data.vehicle_number,
        ParkingEvent.exit_time == None
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="No active parking event found for this vehicle")

    # Extend time limit
    event.allowed_duration_hours += data.extension_hours
    db.commit()
    db.refresh(event)
    return event


@app.get("/api/events", tags=["Sensor Events"])
def list_events(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get paginated parking events, ordered by most recent first, with lot and space details."""
    # Get total count
    total = db.query(ParkingEvent).count()
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get paginated events
    events = db.query(ParkingEvent).order_by(ParkingEvent.entry_time.desc()).offset(offset).limit(per_page).all()
    
    result = []
    for event in events:
        result.append({
            "id": event.id,
            "space_id": event.space_id,
            "lot_name": event.space.lot.name,
            "space_number": event.space.space_number,
            "vehicle_number": event.vehicle_number,
            "entry_time": event.entry_time,
            "exit_time": event.exit_time,
            "duration_hours": event.duration_hours,
            "allowed_duration_hours": event.allowed_duration_hours
        })
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return {
        "items": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


# ══════════════════════════════════════════════════════════════════
# ALERT ENDPOINTS (Violations & Notifications)
# ══════════════════════════════════════════════════════════════════

@app.post("/api/alerts", response_model=AlertResponse, tags=["Alerts"], status_code=201)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    """Create a new parking alert/violation manually."""
    space = db.query(ParkingSpace).filter(ParkingSpace.id == alert.space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Parking space not found")

    db_alert = Alert(
        space_id=alert.space_id,
        alert_type=alert.alert_type,
        message=alert.message
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


@app.get("/api/alerts", response_model=List[AlertResponse], tags=["Alerts"])
def list_alerts(
    is_resolved: Optional[bool] = Query(None, description="Filter: True for resolved, False for unresolved"),
    db: Session = Depends(get_db)
):
    """List all alerts with optional filter by resolution status."""
    query = db.query(Alert)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)
    return query.order_by(Alert.created_at.desc()).all()


@app.put("/api/alerts/{alert_id}/resolve", response_model=AlertResponse, tags=["Alerts"])
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as resolved."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_resolved = True
    db.commit()
    db.refresh(alert)
    return alert


# ══════════════════════════════════════════════════════════════════
# ANALYTICS & DASHBOARD ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@app.get("/api/dashboard/summary", response_model=DashboardSummary, tags=["Analytics"])
def get_summary(db: Session = Depends(get_db)):
    """
    Real-time parking dashboard summary.
    Returns total spaces, occupied, available - grouped by lot.
    """
    lots = db.query(ParkingLot).all()
    lot_summaries = []
    total_spaces = 0
    total_occupied = 0

    for lot in lots:
        spaces = db.query(ParkingSpace).filter(ParkingSpace.lot_id == lot.id).all()
        occupied = sum(1 for s in spaces if s.is_occupied)
        available = len(spaces) - occupied

        lot_summaries.append(LotSummary(
            name=lot.name,
            location=lot.location,
            total=len(spaces),
            occupied=occupied,
            available=available
        ))

        total_spaces += len(spaces)
        total_occupied += occupied

    return DashboardSummary(
        total_spaces=total_spaces,
        occupied=total_occupied,
        available=total_spaces - total_occupied,
        lots=lot_summaries
    )


@app.get("/api/analytics/weekly", response_model=WeeklyAnalytics, tags=["Analytics"])
def weekly_analytics(db: Session = Depends(get_db)):
    """
    Weekly analytics report generated by Pandas.
    Includes: daily entries, peak hours, avg duration, lot comparison, overstay count.
    """
    return get_weekly_analytics(db)


# ─── Serve Dashboard ─────────────────────────────────────────────
@app.get("/", tags=["Dashboard"])
def serve_root(request: Request):
    """Always return the admin login as the application's first page."""
    return FileResponse("static/admin.html")

@app.get("/admin", tags=["Admin"])
def serve_admin_login(request: Request):
    """Returns the admin login page or redirects to public dashboard if already logged in."""
    token = request.cookies.get("admin_token")
    if token and verify_token(token):
        return RedirectResponse("/dashboard")
    return FileResponse("static/admin.html")


@app.get("/dashboard", tags=["Dashboard"])
def serve_public_dashboard():
    """Returns the public Smart City Parking dashboard page."""
    return FileResponse("static/index.html")


@app.get("/admin-dashboard", tags=["Admin"])
def serve_admin_dashboard(request: Request):
    """Returns the admin dashboard page only if a valid admin token cookie is present."""
    token = request.cookies.get("admin_token")
    if token and verify_token(token):
        return FileResponse("static/admin-dashboard.html")
    return RedirectResponse("/admin")

# Serve static files (CSS, JS) - mounted after routes
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Run the server ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
