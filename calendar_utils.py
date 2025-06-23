
from datetime import datetime, timedelta
from googleapiclient.discovery import build

START_HOUR = 8
END_HOUR = 20
SLOT_DURATION = timedelta(minutes=30)

def get_calendar_service():
    from google.oauth2 import service_account
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = 'credentials.json'
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    return service

def is_time_slot_available(service, calendar_id, start_time, duration):
    end_time = start_time + duration
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_time.isoformat() + 'Z',
        timeMax=end_time.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return len(events) == 0

def get_free_slots_for_date(service, calendar_id, date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    start_datetime = datetime.combine(date, datetime.min.time()).replace(hour=START_HOUR)
    end_datetime = datetime.combine(date, datetime.min.time()).replace(hour=END_HOUR)
    slots = []
    current = start_datetime

    while current + SLOT_DURATION <= end_datetime:
        if is_time_slot_available(service, calendar_id, current, SLOT_DURATION):
            slots.append(current.strftime("%H:%M"))
        current += SLOT_DURATION

    return slots

def get_next_available_slots(service, calendar_id, days_ahead=7):
    today = datetime.now().date()
    next_slots = []

    for day_offset in range(days_ahead):
        current_date = today + timedelta(days=day_offset)
        day_slots = get_free_slots_for_date(service, calendar_id, current_date.strftime("%Y-%m-%d"))
        if day_slots:
            next_slots.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "slots": day_slots
            })

    return next_slots
