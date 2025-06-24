WORK_HOURS = {
    "mon": ["08:00", "18:00"],
    "tue": ["08:00", "18:00"],
    "wed": ["08:00", "18:00"],
    "thu": ["08:00", "18:00"],
    "fri": ["08:00", "18:00"]
}

import os
import json

SERVICE_ACCOUNT_INFO = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
CALENDAR_ID = "ab771cebfa8568bc7bf235ebffe22cca74458429c19dce4590e01a7bd1b07182@group.calendar.google.com"

SLOT_DURATION_MINUTES = 30
