import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, time
from dateutil import parser
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI(title="Neuratek Booking API")

# OPENING HOURS
OPEN_FROM = time(8, 0)
OPEN_TO = time(16, 0)
SLOT_DURATION = 60  # minutes

# LOAD GOOGLE CREDS
def get_calendar_service():
    json_data = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not json_data:
        raise Exception("GOOGLE_SERVICE_ACCOUNT_JSON missing.")

    credentials = service_account.Credentials.from_service_account_info(
        eval(json_data),
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=credentials)


CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")


# ------------------ MODELS ------------------

class BookRequest(BaseModel):
    name: str
    company: str
    phone: str
    date: str
    time: str
    timezone: str = "Europe/Berlin"
    notes: str | None = None


class AvailabilityRequest(BaseModel):
    date: str
    time: str
    timezone: str = "Europe/Berlin"


class FreeSlotsRequest(BaseModel):
    date: str
    timezone: str = "Europe/Berlin"


class NextFreeSlotsRequest(BaseModel):
    count: int = 3
    timezone: str = "Europe/Berlin"


class DeleteRequest(BaseModel):
    event_id: str


# ------------------ UTILITIES ------------------

def generate_slots_for_day(date_obj):
    """Generate all valid 1h slots inside opening hours."""
    slots = []
    start_dt = datetime.combine(date_obj, OPEN_FROM)
    end_dt = datetime.combine(date_obj, OPEN_TO)

    while start_dt < end_dt:
        slot_end = start_dt + timedelta(minutes=SLOT_DURATION)
        if slot_end <= end_dt:
            slots.append((start_dt, slot_end))
        start_dt = slot_end

    return slots


def get_busy_times(service, date_obj, tz):
    """Google Calendar busy blocks"""
    start_of_day = tz.localize(datetime.combine(date_obj, time(0, 0))).isoformat()
    end_of_day = tz.localize(datetime.combine(date_obj, time(23, 59, 59))).isoformat()

    fb = service.freebusy().query(
        body={
            "timeMin": start_of_day,
            "timeMax": end_of_day,
            "items": [{"id": CALENDAR_ID}]
        }
    ).execute()

    busy = fb["calendars"][CALENDAR_ID]["busy"]
    blocks = [(parser.parse(b["start"]), parser.parse(b["end"])) for b in busy]
    return blocks


def is_free(slot_start, slot_end, busy_blocks):
    for b_start, b_end in busy_blocks:
        if slot_start < b_end and slot_end > b_start:
            return False
    return True


# ------------------ ENDPOINTS ------------------

@app.post("/book")
def book(req: BookRequest):
    service = get_calendar_service()

    tz = pytz.timezone(req.timezone)
    date_obj = parser.parse(req.date).date()
    start_dt = tz.localize(parser.parse(f"{req.date} {req.time}"))
    end_dt = start_dt + timedelta(minutes=SLOT_DURATION)

    # Check opening hours
    if not (OPEN_FROM <= start_dt.time() < OPEN_TO):
        raise HTTPException(400, "Outside opening hours.")

    # Check availability
    busy_blocks = get_busy_times(service, date_obj, tz)
    if not is_free(start_dt, end_dt, busy_blocks):
        raise HTTPException(400, "Slot not free.")

    event = {
        "summary": f"Termin mit {req.name} ({req.company})",
        "description": f"Telefon: {req.phone}\nNotizen: {req.notes}",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": req.timezone},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": req.timezone},
    }

    created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

    return {
        "status": "ok",
        "event_id": created["id"],
        "html_link": created["htmlLink"]
    }


@app.post("/check-availability")
def check_availability(req: AvailabilityRequest):
    service = get_calendar_service()

    tz = pytz.timezone(req.timezone)
    date_obj = parser.parse(req.date).date()
    start_dt = tz.localize(parser.parse(f"{req.date} {req.time}"))
    end_dt = start_dt + timedelta(minutes=SLOT_DURATION)

    busy_blocks = get_busy_times(service, date_obj, tz)

    return {"available": is_free(start_dt, end_dt, busy_blocks)}


@app.post("/free-slots")
def free_slots(req: FreeSlotsRequest):
    service = get_calendar_service()

    tz = pytz.timezone(req.timezone)
    date_obj = parser.parse(req.date).date()

    busy_blocks = get_busy_times(service, date_obj, tz)
    slots = generate_slots_for_day(date_obj)

    free = []
    for s_start, s_end in slots:
        s_start = tz.localize(s_start)
        s_end = tz.localize(s_end)
        if is_free(s_start, s_end, busy_blocks):
            free.append({
                "start": s_start.isoformat(),
                "end": s_end.isoformat()
            })

    return {"date": req.date, "free_slots": free}


@app.post("/next-free")
def next_free(req: NextFreeSlotsRequest):
    service = get_calendar_service()

    tz = pytz.timezone(req.timezone)
    found = []
    day = datetime.now(tz).date()

    while len(found) < req.count:
        busy = get_busy_times(service, day, tz)
        slots = generate_slots_for_day(day)

        for s_start, s_end in slots:
            s_start = tz.localize(s_start)
            s_end = tz.localize(s_end)
            if is_free(s_start, s_end, busy):
                found.append({
                    "date": str(day),
                    "start": s_start.isoformat(),
                    "end": s_end.isoformat()
                })
                if len(found) == req.count:
                    break

        day += timedelta(days=1)

    return {"next_free_slots": found}


@app.post("/delete")
def delete(req: DeleteRequest):
    service = get_calendar_service()
    try:
        service.events().delete(calendarId=CALENDAR_ID, eventId=req.event_id).execute()
        return {"status": "deleted"}
    except Exception:
        raise HTTPException(400, "Invalid event_id.")
