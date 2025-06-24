
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from calendar_utils import (
    is_slot_free, book_appointment, delete_appointment,
    get_free_slots_for_day, get_next_free_slots
)
from datetime import datetime

app = FastAPI()

class BookingRequest(BaseModel):
    date: str
    time: str
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

class NextFreeRequest(BaseModel):
    count: int = 3

@app.post("/check-availability")
def check_availability(req: AvailabilityRequest):
    dt = datetime.fromisoformat(f"{req.date}T{req.time}")
    available = is_slot_free(dt)
    return {"available": available}

@app.post("/book")
def book(req: BookingRequest):
    dt = datetime.fromisoformat(f"{req.date}T{req.time}")
    success = book_appointment(dt, req.name)
    if not success:
        raise HTTPException(status_code=409, detail="Time slot already booked")
    return {"status": "booked"}

@app.post("/delete")
def delete(req: DeleteRequest):
    dt = datetime.fromisoformat(f"{req.date}T{req.time}")
    success = delete_appointment(dt, req.name)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"status": "deleted"}

@app.post("/free-slots")
def free_slots(req: FreeSlotsRequest):
    free = get_free_slots_for_day(req.date, None)
    return {"free_slots": free}

@app.post("/next-free")
def next_free():
    slots = get_next_free_slots()
    return {"next_slots": slots}
