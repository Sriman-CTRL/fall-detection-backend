import os
from datetime import datetime, timezone

from fastapi import FastAPI, Depends
from pydantic import BaseModel

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    desc
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1),
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# ============================================================
# DATABASE TABLE
# ============================================================

class FallEventDB(Base):
    __tablename__ = "fall_events"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    device_id = Column(
        String(100),
        nullable=False
    )

    event = Column(
        String(50),
        nullable=False
    )

    fall_probability = Column(
        Float,
        nullable=False
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False
    )


# Create the table automatically if it doesn't exist
Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Fall Detection IoT Backend"
)


# ============================================================
# REQUEST MODEL
# ============================================================

class FallEvent(BaseModel):
    device_id: str
    event: str
    fall_probability: float


# ============================================================
# DATABASE SESSION
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Fall Detection Backend is running"
    }


# ============================================================
# POST FALL EVENT
# ============================================================

@app.post("/api/fall-event")
def receive_fall_event(
    data: FallEvent,
    db: Session = Depends(get_db)
):

    # Determine event status
    if data.event == "FALL_CONFIRMED":
        status = "CONFIRMED"

    elif data.event == "FALL_DETECTED":
        status = "POSSIBLE"

    else:
        status = "UNKNOWN"


    # Current UTC time
    current_time = datetime.now(timezone.utc)


    # Create database record
    fall_event = FallEventDB(
        device_id=data.device_id,
        event=data.event,
        fall_probability=data.fall_probability,
        timestamp=current_time,
        status=status
    )


    # Save to PostgreSQL
    db.add(fall_event)
    db.commit()
    db.refresh(fall_event)


    # Print to server logs
    print("\n==============================")
    print("       FALL EVENT RECEIVED")
    print("==============================")
    print("Database ID:", fall_event.id)
    print("Device ID:", fall_event.device_id)
    print("Event:", fall_event.event)
    print("Probability:", fall_event.fall_probability)
    print("Status:", fall_event.status)
    print("Timestamp:", fall_event.timestamp)


    return {
        "success": True,
        "message": "Fall event saved successfully",
        "id": fall_event.id,
        "device_id": fall_event.device_id,
        "event": fall_event.event,
        "fall_probability": fall_event.fall_probability,
        "timestamp": fall_event.timestamp,
        "status": fall_event.status
    }


# ============================================================
# GET FALL EVENTS
# ============================================================

@app.get("/api/fall-events")
def get_fall_events(
    db: Session = Depends(get_db)
):

    events = (
        db.query(FallEventDB)
        .order_by(desc(FallEventDB.timestamp))
        .all()
    )


    return [
        {
            "id": event.id,
            "device_id": event.device_id,
            "event": event.event,
            "fall_probability": event.fall_probability,
            "timestamp": event.timestamp,
            "status": event.status
        }
        for event in events
    ]