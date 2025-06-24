from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from calendar_utils import get_free_slots_for_day, get_next_free_slots, book_slot, delete_slot, is_slot_free

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FreeSlotsRequest(BaseModel):
    date: str

class NextFreeRequest(BaseModel):
    count: int = 3

class BookRequest(BaseModel):
    date: str
    time: str
    name: str

class DeleteRequest(BaseModel):
    date: str
    time: str

class SlotCheckRequest(BaseModel):
    date: str
    time: str

@app.post("/free-slots")
def free_slots(req: FreeSlotsRequest):
    free = get_free_slots_for_day(req.date, None)
    return {"free_slots": free}

@app.post("/next-free")
def next_free(req: NextFreeRequest):
    slots = get_next_free_slots(req.count)
    return {"next_slots": slots}

@app.post("/book-slot")
def book(req: BookRequest):
    result = book_slot(req.date, req.time, req.name)
    return {"result": result}

@app.post("/delete-slot")
def delete(req: DeleteRequest):
    result = delete_slot(req.date, req.time)
    return {"result": result}

@app.post("/check-slot")
def check(req: SlotCheckRequest):
    result = is_slot_free(req.date, req.time)
    return {"is_free": result}