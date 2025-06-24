from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta, time
from config import WORK_HOURS, SERVICE_ACCOUNT_FILE, CALENDAR_ID, SLOT_DURATION_MINUTES

SCOPES = ["https://www.googleapis.com/auth/calendar"]
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("calendar", "v3", credentials=credentials)

weekday_map = {
    0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"
}

def get_events(date):
    start_datetime = datetime.strptime(date, "%Y-%m-%d")
    end_datetime = start_datetime + timedelta(days=1)
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_datetime.isoformat() + 'Z',
        timeMax=end_datetime.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

def get_free_slots_for_day(date, _):
    weekday = datetime.strptime(date, "%Y-%m-%d").weekday()
    day_key = weekday_map.get(weekday)
    if day_key not in WORK_HOURS:
        return []

    start_str, end_str = WORK_HOURS[day_key]
    start_time = datetime.strptime(start_str, "%H:%M").time()
    end_time = datetime.strptime(end_str, "%H:%M").time()

    events = get_events(date)
    busy_times = [(datetime.strptime(e["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z").time(),
                   datetime.strptime(e["end"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z").time())
                  for e in events if "dateTime" in e["start"]]

    current = datetime.combine(datetime.strptime(date, "%Y-%m-%d"), start_time)
    end_dt = datetime.combine(datetime.strptime(date, "%Y-%m-%d"), end_time)
    delta = timedelta(minutes=SLOT_DURATION_MINUTES)
    free_slots = []

    while current + delta <= end_dt:
        slot_start = current.time()
        slot_end = (current + delta).time()
        if not any(bs <= slot_start < be or bs < slot_end <= be for bs, be in busy_times):
            free_slots.append(current.strftime("%H:%M"))
        current += delta

    return free_slots

def get_next_free_slots(count):
    today = datetime.now().date()
    slots = []
    checked_days = 0
    while len(slots) < count and checked_days < 14:
        date_str = today.strftime("%Y-%m-%d")
        day_slots = get_free_slots_for_day(date_str, None)
        for slot in day_slots:
            if len(slots) < count:
                slots.append({"date": date_str, "time": slot})
        today += timedelta(days=1)
        checked_days += 1
    return slots

def book_slot(date, time_str, name):
    start = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
    end = start + timedelta(minutes=SLOT_DURATION_MINUTES)
    event = {
        "summary": f"Termin mit {name}",
        "start": {"dateTime": start.isoformat(), "timeZone": "Europe/Berlin"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Europe/Berlin"}
    }
    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return "success"

def delete_slot(date, time_str):
    events = get_events(date)
    for e in events:
        start_time = datetime.strptime(e["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M")
        if start_time == time_str:
            service.events().delete(calendarId=CALENDAR_ID, eventId=e["id"]).execute()
            return "deleted"
    return "not found"

def is_slot_free(date, time_str):
    free_slots = get_free_slots_for_day(date, None)
    return time_str in free_slots