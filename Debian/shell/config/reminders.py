from datetime import timedelta

REMINDERS_JSON_PATH = "reminders.json"

ALL_DAY_REMINDER_DELAY = 30  # seconds

NEXT_DAY_REMINDER_DELAY = 60  # seconds

DELETE_REMINDER_DELTA = timedelta(days=90)

REMINDER_INTERVAL_DELTAS = [
    timedelta(minutes=0),
    timedelta(minutes=5),
    timedelta(minutes=10),
    timedelta(minutes=30),
    timedelta(hours=1),
]
