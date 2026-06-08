"""
Parking Sensor Simulator

Simulates 1 week of IoT parking sensor data:
    - Creates 3 parking lots (Mall, Airport, Hospital)
    - Creates 100 spaces per lot (300 total)
    - Generates realistic, chronological, overlap-free parking events over the last 7 days
    - Tracks space occupancy status accurately and handles overstay limits dynamically

Runs once at server startup - no separate terminal needed.
"""

import random
from datetime import datetime, timedelta
from database import SessionLocal, ParkingLot, ParkingSpace, ParkingEvent, Alert


# ─── Sample Data ──────────────────────────────────────────────────
LOTS = [
    {"name": "City Mall Parking", "location": "MG Road, Bangalore", "total_spaces": 100},
    {"name": "Airport Parking", "location": "Kempegowda International Airport", "total_spaces": 100},
    {"name": "Hospital Parking", "location": "Jayanagar, Bangalore", "total_spaces": 100},
]

# Indian state codes for realistic vehicle numbers
STATE_CODES = ["KA", "MH", "TN", "DL", "AP", "TS", "KL", "GJ"]


def generate_vehicle_number():
    """Generate a random Indian vehicle number like KA-01-AB-1234."""
    state = random.choice(STATE_CODES)
    district = str(random.randint(1, 99)).zfill(2)
    letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
    number = str(random.randint(1000, 9999))
    return f"{state}-{district}-{letters}-{number}"


def seed_data():
    """Generate 1 week of simulated parking data."""
    db = SessionLocal()

    # Check if data already exists and is fresh (from today or later)
    if db.query(ParkingLot).count() > 0:
        # Get the latest event date
        latest_event = db.query(ParkingEvent).order_by(ParkingEvent.entry_time.desc()).first()
        if latest_event:
            latest_event_date = latest_event.entry_time.date()
            today = datetime.now().date()
            
            # If latest event is from today or later, data is fresh - skip regeneration
            if latest_event_date >= today:
                print("[OK] Data already exists and is current, skipping simulation.")
                db.close()
                return
            
            # Data is stale - clear and regenerate
            print("[*] Data is stale, regenerating...")
            db.query(ParkingEvent).delete()
            db.query(Alert).delete()
            db.query(ParkingSpace).delete()
            db.query(ParkingLot).delete()
            db.commit()
        else:
            # Lots exist but no events - treat as stale
            print("[*] No events found, regenerating...")
            db.query(ParkingEvent).delete()
            db.query(Alert).delete()
            db.query(ParkingSpace).delete()
            db.query(ParkingLot).delete()
            db.commit()

    print("[*] Starting parking simulation...")

    # ─── Step 1: Create parking lots ─────────────────────────────
    lots = []
    for lot_data in LOTS:
        lot = ParkingLot(**lot_data)
        db.add(lot)
        lots.append(lot)
    db.commit()
    print(f"  [+] Created {len(lots)} parking lots")

    # ─── Step 2: Create parking spaces ───────────────────────────
    all_spaces = []
    for lot in lots:
        for i in range(1, lot.total_spaces + 1):
            row = chr(64 + ((i - 1) // 10) + 1)  # A, B, C...
            num = ((i - 1) % 10) + 1
            space = ParkingSpace(
                lot_id=lot.id,
                space_number=f"{row}{num}",
                is_occupied=False
            )
            db.add(space)
            all_spaces.append(space)
    db.commit()
    print(f"  [+] Created {len(all_spaces)} parking spaces")

    # ─── Step 3: Generate raw parking events for last 7 days ─────────
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    raw_events = []

    for day_offset in range(8):
        day = week_ago + timedelta(days=day_offset)

        # More events on weekdays, fewer on weekends
        if day.weekday() < 5:  # Monday-Friday
            num_events = random.randint(60, 90)
        else:  # Saturday-Sunday
            num_events = random.randint(30, 50)

        for _ in range(num_events):
            # Choose a lot based on custom traffic weights (Mall: 50%, Airport: 35%, Hospital: 15%)
            chosen_lot = random.choices(lots, weights=[0.50, 0.35, 0.15], k=1)[0]
            vehicle = generate_vehicle_number()

            # Random entry hour (weighted towards morning and evening)
            hour_weights = [1,1,1,1,1,2,3,5,8,9,7,6,5,5,6,7,8,9,7,5,3,2,1,1]
            hour = random.choices(range(24), weights=hour_weights, k=1)[0]
            minute = random.randint(0, 59)

            entry_time = day.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # Don't create entry events in the future
            if entry_time > now:
                continue

            # Random parking duration (30 mins to 8 hours)
            # 10% chance of overstay (>4 hours) for violation detection
            if random.random() < 0.1:
                duration = random.uniform(4.5, 8.0)  # Overstay
            else:
                duration = random.uniform(0.5, 4.0)   # Normal

            exit_time = entry_time + timedelta(hours=duration)

            # Don't create exit events in the future
            if exit_time > now:
                exit_time = None
                duration = None

            raw_events.append({
                "lot_id": chosen_lot.id,
                "vehicle_number": vehicle,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "duration": duration
            })

    # Sort all events chronologically by entry_time
    raw_events.sort(key=lambda x: x["entry_time"])

    # ─── Step 4: Chronologically assign spaces and save events ───
    # Tracks when each space becomes free
    space_last_exit = {space.id: week_ago - timedelta(days=1) for space in all_spaces}
    events_count = 0
    occupied_count = 0

    for event_data in raw_events:
        # Get all spaces for the chosen lot
        lot_spaces = [s for s in all_spaces if s.lot_id == event_data["lot_id"]]
        
        # Filter for spaces that are free at the event's entry time
        available_spaces = [
            s for s in lot_spaces 
            if space_last_exit[s.id] <= event_data["entry_time"]
        ]
        
        if not available_spaces:
            # Lot is full at this point in time, skip event (realistic)
            continue
            
        # Choose a random available space
        space = random.choice(available_spaces)
        
        # Update when this space becomes free
        if event_data["exit_time"] is None:
            # Still parked, so it stays occupied indefinitely for this seeding run
            space_last_exit[space.id] = datetime.max
        else:
            space_last_exit[space.id] = event_data["exit_time"]
            
        # Write to database
        db_event = ParkingEvent(
            space_id=space.id,
            vehicle_number=event_data["vehicle_number"],
            entry_time=event_data["entry_time"],
            exit_time=event_data["exit_time"],
            duration_hours=round(event_data["duration"], 2) if event_data["duration"] is not None else None,
            allowed_duration_hours=4.0
        )
        db.add(db_event)
        events_count += 1

    # ─── Step 5: Sync space occupancy status with database ────────
    for space in all_spaces:
        if space_last_exit[space.id] == datetime.max:
            space.is_occupied = True
            occupied_count += 1
        else:
            space.is_occupied = False

    db.commit()
    db.close()

    print(f"  [+] Generated {events_count} parking events over 7 days")
    print(f"  [+] {occupied_count} spaces currently occupied")
    print("[DONE] Simulation complete!\n")
