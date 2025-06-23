from datetime import datetime, timedelta
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'fitnessstudio-sonnenberg-06c2e2dfd96c.json'
CALENDAR_ID = 'primary'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

OPENING_HOUR = 9
CLOSING_HOUR = 18
SLOT_DURATION_MINUTES = 30

def is_slot_free(date_str, time_str):
    tz = pytz.timezone('Europe/Berlin')
    start_datetime = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))
    end_datetime = start_datetime + timedelta(minutes=SLOT_DURATION_MINUTES)

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_datetime.isoformat(),
        timeMax=end_datetime.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return len(events_result.get('items', [])) == 0

def get_free_slots_for_date(date_str):
    tz = pytz.timezone('Europe/Berlin')
    date = datetime.strptime(date_str, "%Y-%m-%d")
    slots = []

    for hour in range(OPENING_HOUR, CLOSING_HOUR):
        for minute in [0, 30]:
            dt = tz.localize(datetime(date.year, date.month, date.day, hour, minute))
            end_dt = dt + timedelta(minutes=SLOT_DURATION_MINUTES)

            events = service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=dt.isoformat(),
                timeMax=end_dt.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            if not events.get('items'):
                slots.append(dt.strftime("%H:%M"))

    return slots

def get_next_available_slots():
    tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(tz)
    slots = []

    for days_ahead in range(7):
        day = now + timedelta(days=days_ahead)
        date_str = day.strftime("%Y-%m-%d")
        day_slots = get_free_slots_for_date(date_str)

        for time in day_slots:
            slots.append({"date": date_str, "time": time})
            if len(slots) >= 5:
                return slots

    return slots
