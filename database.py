"""
Database models and setup using SQLAlchemy ORM with SQLite.

Tables:
    - ParkingLot: Parking lots in the city (e.g., Mall, Airport)
    - ParkingSpace: Individual spaces inside each lot
    - ParkingEvent: Every vehicle entry/exit recorded by IoT sensors
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# SQLite database - creates a file called parking.db
DATABASE_URL = "sqlite:///parking.db"

# Create engine (connects to the database)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session factory (used to interact with the DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


# ─── Table 1: Parking Lots ───────────────────────────────────────
class ParkingLot(Base):
    __tablename__ = "parking_lots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)          # e.g., "City Mall"
    location = Column(String, nullable=False)       # e.g., "MG Road, Bangalore"
    total_spaces = Column(Integer, nullable=False)  # e.g., 20

    # Relationship: one lot has many spaces
    spaces = relationship("ParkingSpace", back_populates="lot")


# ─── Table 2: Parking Spaces ─────────────────────────────────────
class ParkingSpace(Base):
    __tablename__ = "parking_spaces"

    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey("parking_lots.id"), nullable=False)
    space_number = Column(String, nullable=False)   # e.g., "A1", "A2"
    is_occupied = Column(Boolean, default=False)     # True = car parked

    # Relationships
    lot = relationship("ParkingLot", back_populates="spaces")
    events = relationship("ParkingEvent", back_populates="space")


# ─── Table 3: Parking Events (IoT Sensor Data) ───────────────────
class ParkingEvent(Base):
    __tablename__ = "parking_events"

    id = Column(Integer, primary_key=True, index=True)
    space_id = Column(Integer, ForeignKey("parking_spaces.id"), nullable=False)
    vehicle_number = Column(String, nullable=False)  # e.g., "KA-01-AB-1234"
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)       # None if still parked
    duration_hours = Column(Float, nullable=True)     # Calculated on exit
    allowed_duration_hours = Column(Float, default=4.0, nullable=False)  # Default allowance is 4 hours

    # Relationship
    space = relationship("ParkingSpace", back_populates="events")


# ─── Table 4: Alerts (Violations & Notifications) ────────────────
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    space_id = Column(Integer, ForeignKey("parking_spaces.id"), nullable=False)
    alert_type = Column(String, nullable=False)       # "overstay", "unauthorized", "double_parking"
    message = Column(String, nullable=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    # Relationship
    space = relationship("ParkingSpace")


# ─── Create all tables ───────────────────────────────────────────
def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


# ─── Get database session ────────────────────────────────────────
def get_db():
    """Dependency that provides a database session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
