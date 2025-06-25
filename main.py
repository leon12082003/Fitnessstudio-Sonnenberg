from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from calendar_utils import (
    is_slot_free, book_appointment, delete_appointment,
    get_free_slots_for_day, get_next_free_slots
)
from config import CALENDAR_ID
from datetime import datetime

app = FastAPI()

class BookingRequest(BaseModel):
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    name: str

class AvailabilityRequest(BaseModel):
    date: str
    time: str

class DeleteRequest(BaseModel):
    date: str
    time: str
    name: str

class FreeSlotsRequest(BaseModel):
    date: str


@app.post("/check-availability")
def check_availability(req: AvailabilityRequest):
    dt = datetime.fromisoformat(f"{req.date}T{req.time}")
    available = is_slot_free(CALENDAR_ID, dt)
    if not available:
        # negativer Fall → 409 Conflict
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot not available"
        )
    # positiver Fall → 200 OK
    return {"available": True}


@app.post("/book")
def book(req: BookingRequest):
    dt = datetime.fromisoformat(f"{req.date}T{req.time}")
    success = book_appointment(CALENDAR_ID, dt, req.name)
    if not success:
        # negativer Fall → 409 Conflict
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot already booked"
        )
    # positiver Fall → 200 OK
    return {"status": "booked"}


@app.post("/delete")
def delete(req: DeleteRequest):
    dt = datetime.fromisoformat(f"{req.date}T{req.time}")
    success = delete_appointment(CALENDAR_ID, dt, req.name)
    if not success:
        # negativer Fall → 404 Not Found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    # positiver Fall → 200 OK
    return {"status": "deleted"}


@app.post("/free-slots")
def free_slots(req: FreeSlotsRequest):
    free = get_free_slots_for_day(CALENDAR_ID, req.date)
    if not free:
        # negativer Fall → 204 No Content
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No free slots"
        )
    # positiver Fall → 200 OK
    return {"free_slots": free}


@app.get("/next-free")
def next_free():
    slots = get_next_free_slots(CALENDAR_ID)
    # immer mindestens ein Slot vorhanden → 200 OK
    return {"next_slots": slots}
