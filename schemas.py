"""
Pydantic Schemas for request/response validation.

These schemas:
    - Validate incoming request data (POST/PUT bodies)
    - Define response structure (what the API returns)
    - Auto-generate Swagger documentation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════
# PARKING LOT SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class ParkingLotCreate(BaseModel):
    """Schema for creating a new parking lot (POST request body)."""
    name: str = Field(..., example="City Mall Parking")
    location: str = Field(..., example="MG Road, Bangalore")
    total_spaces: int = Field(..., gt=0, example=20)

class ParkingLotUpdate(BaseModel):
    """Schema for updating a parking lot (PUT request body). All fields optional."""
    name: Optional[str] = Field(None, example="City Mall Parking - Updated")
    location: Optional[str] = Field(None, example="MG Road, Bangalore")
    total_spaces: Optional[int] = Field(None, gt=0, example=25)

class ParkingLotResponse(BaseModel):
    """Schema for parking lot response."""
    id: int
    name: str
    location: str
    total_spaces: int

    class Config:
        from_attributes = True  # Allows converting SQLAlchemy model to Pydantic


# ═══════════════════════════════════════════════════════════════════
# PARKING SPACE SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class ParkingSpaceResponse(BaseModel):
    """Schema for parking space response."""
    id: int
    lot_id: int
    space_number: str
    is_occupied: bool

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════
# SENSOR EVENT SCHEMAS (IoT Sensor Data)
# ═══════════════════════════════════════════════════════════════════

class VehicleEntryRequest(BaseModel):
    """Schema for vehicle entry sensor event (POST body)."""
    space_id: int = Field(..., example=1)
    vehicle_number: str = Field(..., example="KA-01-AB-1234")

class VehicleExitRequest(BaseModel):
    """Schema for vehicle exit sensor event (POST body)."""
    space_id: int = Field(..., example=1)
    vehicle_number: str = Field(..., example="KA-01-AB-1234")

class VehicleExtensionRequest(BaseModel):
    """Schema for vehicle parking duration extension request (POST body)."""
    space_id: int = Field(..., example=1)
    vehicle_number: str = Field(..., example="KA-01-AB-1234")
    extension_hours: float = Field(..., gt=0, example=2.0)

class ParkingEventResponse(BaseModel):
    """Schema for parking event response."""
    id: int
    space_id: int
    vehicle_number: str
    entry_time: datetime
    exit_time: Optional[datetime]
    duration_hours: Optional[float]
    allowed_duration_hours: float

    class Config:
        from_attributes = True


class ParkingEventDetailsResponse(BaseModel):
    """Schema for detailed parking event response, including lot and space names."""
    id: int
    space_id: int
    lot_name: str
    space_number: str
    vehicle_number: str
    entry_time: datetime
    exit_time: Optional[datetime]
    duration_hours: Optional[float]
    allowed_duration_hours: float

    class Config:
        from_attributes = True



# ═══════════════════════════════════════════════════════════════════
# ALERT SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class AlertCreate(BaseModel):
    """Schema for creating an alert (POST body)."""
    space_id: int = Field(..., example=1)
    alert_type: str = Field(..., example="overstay", description="Type: overstay, unauthorized, double_parking")
    message: str = Field(..., example="Vehicle KA-01-AB-1234 parked for more than 4 hours")

class AlertResponse(BaseModel):
    """Schema for alert response."""
    id: int
    space_id: int
    alert_type: str
    message: str
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD & ANALYTICS SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class LotSummary(BaseModel):
    """Summary for a single parking lot."""
    name: str
    location: str
    total: int
    occupied: int
    available: int

class DashboardSummary(BaseModel):
    """Schema for dashboard summary response."""
    total_spaces: int
    occupied: int
    available: int
    lots: List[LotSummary]

class DailyEntry(BaseModel):
    date: str
    entries: int

class PeakHour(BaseModel):
    hour: int
    entries: int

class LotComparison(BaseModel):
    lot_name: str
    total_entries: int
    avg_duration: float

class WeeklyAnalytics(BaseModel):
    """Schema for weekly analytics response."""
    daily_entries: List[DailyEntry]
    peak_hours: List[PeakHour]
    avg_duration_hours: float
    lot_comparison: List[LotComparison]
    overstay_count: int
    total_events: int
