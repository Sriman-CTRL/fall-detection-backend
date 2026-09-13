from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone

app = FastAPI(title="Fall Detection IoT Backend")


class FallEvent(BaseModel):
    device_id: str
    event: str
    fall_probability: float


@app.get("/")
def root():
    return {
        "message": "Fall Detection Backend is running"
    }


@app.post("/api/fall-event")
def receive_fall_event(data: FallEvent):

    print("\n==============================")
    print("       FALL EVENT RECEIVED")
    print("==============================")

    print("Device ID:", data.device_id)
    print("Event:", data.event)
    print("Probability:", data.fall_probability)

    return {
        "success": True,
        "message": "Fall event received",
        "device_id": data.device_id,
        "event": data.event,
        "fall_probability": data.fall_probability,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }