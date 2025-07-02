from fabric.core.service import Service, Property, Signal
from fabric.utils.helpers import invoke_repeater
from gi.repository import GLib

from util.singleton import Singleton
from config.reminders import (
    REMINDERS_JSON_PATH,
    ALL_DAY_REMINDER_DELAY,
    REMINDER_INTERVAL_DELTAS,
)
from config.storage import STORAGE_DIRECTORY
from services.notifications import NotificationService
from util.helpers import get_user_login_name, get_system_node_name
from services.calendar import CalendarService

from pathlib import Path
import json
from loguru import logger
import uuid
from datetime import date as Date, time as Time, datetime as Datetime


class Reminder:
    notification_service: NotificationService = NotificationService.get_instance()

    def __init__(
        self,
        title: str,
        date: Date,
        time: Time | None = None,
        id: str = str(uuid.uuid4()),
    ):
        self.id = id
        self.title = title
        self.date = date
        self.time = time

    def to_json_obj(self) -> dict:
        return {
            "title": self.title,
            "date": self.date.isoformat(),
            "time": self.time.isoformat(timespec="minutes")
            if self.time is not None
            else None,
        }

    @classmethod
    def from_json_obj(cls, id: str, json_obj: dict):
        title = json_obj["title"]
        date = Date.fromisoformat(json_obj["date"])
        time = (
            Time.fromisoformat(json_obj["time"])
            if json_obj["time"] is not None
            else None
        )

        return cls(title, date, time, id)

    def update(
        self,
        title: str | None = None,
        icon: str | None = None,
        date: Date | None = None,
        time: Time | None = None,
    ) -> None:
        self.title = title if title is not None else self.title
        self.date = date if date is not None else self.date
        self.time = time if time is not None else self.time

    def to_variant(self) -> GLib.Variant:
        system_name = f"{get_user_login_name()}@{get_system_node_name()}"

        return GLib.Variant(
            # s = string, i = signed int, u = unsigned int, as = string array
            "(sisssasasiu)",
            (
                system_name,  # app name
                -1,  # replaces_id
                "",  # app_icon
                self.title,  # summary
                "",  # body
                [],  # actions
                [],  # hints
                -1,  # timeout
                1,  # urgency
            ),
        )

    def send_notification(self):
        self.notification_service.send_internal_notification(self.to_variant())

    def schedule_notifications(self):
        if self.date == Date.today():
            if self.time is None:
                GLib.timeout_add_seconds(ALL_DAY_REMINDER_DELAY, self.send_notification)
            else:
                now = Datetime.now()
                reminder_datetime = Datetime.combine(self.date, self.time)
                if not reminder_datetime <= now:
                    notification_times = [
                        (reminder_datetime - delta).timestamp()
                        for delta in REMINDER_INTERVAL_DELTAS
                    ]

                    timeouts = [
                        timestamp - now.timestamp()
                        for timestamp in notification_times
                        if timestamp >= now.timestamp()
                    ]

                    for timeout in timeouts:
                        GLib.timeout_add_seconds(timeout, self.send_notification)


class ReminderService(Service, Singleton):
    @Signal("changed")
    def changed(self) -> None: ...

    @Property(list[Reminder], flags="readable")
    def reminders(self) -> list[Reminder]:
        return [
            Reminder.from_json_obj(id, json_obj)
            for id, json_obj in self._reminders.items()
        ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._path = None
        self._reminders: dict = None

        self.init_reminders_file()

        self.setup_notifications()

        calendar_service = CalendarService.get_instance()

        calendar_service.connect("notify::today", lambda *_: self.setup_notifications())

    def get_reminders_by_date(self, date: Date) -> list[Reminder]:
        return [reminder for reminder in self.reminders if reminder.date == date]

    def add_reminder(self, reminder: Reminder) -> None:
        """Used to create a new reminder or update an existing reminder."""
        self._reminders[reminder.id] = reminder.to_json_obj()
        self.commit_changes()

    def delete_reminder(self, reminder: Reminder) -> None:
        self._reminders.pop(reminder.id)
        self.commit_changes()

    def is_initialized(self) -> bool:
        """Details whether this service is in a usable state."""
        return self._path is not None and self._reminders is not None

    def commit_changes(self) -> None:
        self.emit("changed")
        self.write_to_disk()

    @logger.catch
    def init_reminders_file(self) -> None:
        self._path = Path(STORAGE_DIRECTORY + REMINDERS_JSON_PATH)

        try:
            if not self._path.exists():
                json.dump(dict(), self._path.open("w"))

            json_file = self._path.open("r+")
        except:
            logger.error("Could not initialize reminders json file.")
        else:
            with json_file:
                self._reminders = json.load(json_file)

    @logger.catch
    def write_to_disk(self) -> None:
        if self.is_initialized():
            json.dump(self._reminders, self._path.open("w"))

    def setup_notifications(self) -> None:
        for reminder in self.reminders:
            reminder.schedule_notifications()
