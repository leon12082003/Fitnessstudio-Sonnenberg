
from datetime import datetime, timedelta, time
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz

SERVICE_ACCOUNT_FILE = 'fitnessstudio-sonnenberg-06c2e2dfd96c.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('calendar', 'v3', credentials=credentials)

TIMEZONE = 'Europe/Berlin'
SLOT_DURATION = timedelta(minutes=30)
OPENING_HOURS = {
    0: (time(8, 0), time(18, 0)),  # Montag
    1: (time(8, 0), time(18, 0)),  # Dienstag
    2: (time(8, 0), time(18, 0)),  # Mittwoch
    3: (time(8, 0), time(18, 0)),  # Donnerstag
    4: (time(8, 0), time(18, 0)),  # Freitag
}

def get_events(start_dt, end_dt):
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

def is_slot_free(start_time, events):
    for event in events:
        event_start = datetime.fromisoformat(event['start']['dateTime']).astimezone(pytz.timezone(TIMEZONE))
        if start_time == event_start:
            return False
    return True

def get_free_slots_for_day(date_str, after_time=None):
    tz = pytz.timezone(TIMEZONE)
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    weekday = date.weekday()
    if weekday not in OPENING_HOURS:
        return []

    start_time, end_time = OPENING_HOURS[weekday]
    start_dt = tz.localize(datetime.combine(date, start_time))
    end_dt = tz.localize(datetime.combine(date, end_time))
    events = get_events(start_dt, end_dt)

    slots = []
    current = start_dt
    while current + SLOT_DURATION <= end_dt:
        if after_time:
            after_dt = datetime.combine(date, datetime.strptime(after_time, "%H:%M").time()).astimezone(tz)
            if current < after_dt:
                current += SLOT_DURATION
                continue
        if is_slot_free(current, events):
            slots.append(current.strftime("%H:%M"))
        current += SLOT_DURATION

    return slots

def get_next_free_slots(count=3):
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).date()
    results = []

    for i in range(14):  # max. 14 Tage im Voraus
        target_date = today + timedelta(days=i)
        slots = get_free_slots_for_day(target_date.strftime("%Y-%m-%d"))
        for time in slots:
            results.append({"date": target_date.strftime("%Y-%m-%d"), "time": time})
            if len(results) == count:
                return results
    return results
