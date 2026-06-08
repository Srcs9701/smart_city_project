"""
Analytics Module using Pandas

Reads parking_events from the database and generates:
    - Day-wise entry count for last 7 days
    - Peak hours (busiest hours of the day)
    - Average parking duration
    - Lot-wise comparison (which lot is busiest)
    - Overstay violations count (parked > 4 hours)
"""

import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import ParkingEvent, ParkingSpace, ParkingLot


def get_weekly_analytics(db: Session) -> dict:
    """Generate weekly analytics report using Pandas."""

    # ─── Step 1: Load data from database into Pandas DataFrame ───
    events = db.query(
        ParkingEvent.id,
        ParkingEvent.space_id,
        ParkingEvent.vehicle_number,
        ParkingEvent.entry_time,
        ParkingEvent.exit_time,
        ParkingEvent.duration_hours,
        ParkingEvent.allowed_duration_hours,
        ParkingSpace.space_number,
        ParkingSpace.lot_id,
        ParkingLot.name.label("lot_name")
    ).join(
        ParkingSpace, ParkingEvent.space_id == ParkingSpace.id
    ).join(
        ParkingLot, ParkingSpace.lot_id == ParkingLot.id
    ).filter(
        ParkingEvent.entry_time >= datetime.now() - timedelta(days=7)
    ).all()

    # If no data, return empty analytics
    if not events:
        return {
            "daily_entries": [],
            "peak_hours": [],
            "avg_duration_hours": 0,
            "lot_comparison": [],
            "overstay_count": 0,
            "total_events": 0
        }

    # Convert query results to DataFrame
    df = pd.DataFrame(events, columns=[
        "id", "space_id", "vehicle_number", "entry_time",
        "exit_time", "duration_hours", "allowed_duration_hours", "space_number", "lot_id", "lot_name"
    ])

    # ─── Step 2: Day-wise entries ─────────────────────────────────
    df["date"] = pd.to_datetime(df["entry_time"]).dt.date
    daily = df.groupby("date").size().reset_index(name="entries")
    daily["date"] = daily["date"].astype(str)
    daily_entries = daily.to_dict(orient="records")

    # ─── Step 3: Peak hours ───────────────────────────────────────
    df["hour"] = pd.to_datetime(df["entry_time"]).dt.hour
    hourly = df.groupby("hour").size().reset_index(name="entries")
    peak_hours = hourly.to_dict(orient="records")

    # ─── Step 4: Average parking duration ─────────────────────────
    avg_duration = round(df["duration_hours"].dropna().mean(), 2)

    # ─── Step 5: Lot-wise comparison ──────────────────────────────
    lot_stats = df.groupby("lot_name").agg(
        total_entries=("id", "count"),
        avg_duration=("duration_hours", "mean")
    ).reset_index()
    lot_stats["avg_duration"] = lot_stats["avg_duration"].round(2)
    lot_comparison = lot_stats.to_dict(orient="records")

    # ─── Step 6: Overstay violations (parked > allowed_duration_hours) ───
    overstay_count = int(df[df["duration_hours"] > df["allowed_duration_hours"]].shape[0])

    return {
        "daily_entries": daily_entries,
        "peak_hours": peak_hours,
        "avg_duration_hours": avg_duration,
        "lot_comparison": lot_comparison,
        "overstay_count": overstay_count,
        "total_events": len(df)
    }
