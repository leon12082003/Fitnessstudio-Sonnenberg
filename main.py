
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from calendar_utils import get_free_slots_for_day, get_next_free_slots

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

@app.post("/free-slots")
def free_slots(req: FreeSlotsRequest):
    free = get_free_slots_for_day(req.date, None)
    return {"free_slots": free}

@app.post("/next-free")
def next_free(req: NextFreeRequest):
    slots = get_next_free_slots(req.count)
    return {"next_slots": slots}
