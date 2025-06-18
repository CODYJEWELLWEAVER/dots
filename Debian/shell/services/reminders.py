from fabric.core.service import Service, Property, Signal

from util.singleton import Singleton
from config.reminders import REMINDERS_JSON_PATH
from config.storage import STORAGE_DIRECTORY

from pathlib import Path
import json
from loguru import logger
import uuid
from datetime import date as Date, time as Time


class Reminder:
    def __init__(
        self,
        title: str,
        icon: str,  # tabler icon markup
        date: Date,
        time: Time | None = None,
        id: str = str(uuid.uuid4()),
    ):
        self.id = id
        self.title = title
        self.icon = icon
        self.date = date
        self.time = time

    def to_json_obj(self):
        return {
            "title": self.title,
            "icon": self.icon,
            "date": self.date.isoformat(),
            "time": self.time.isoformat(timespec="minutes")
            if self.time is not None
            else None,
        }

    @classmethod
    def from_json_obj(cls, id: str, json_obj: dict):
        title = json_obj["title"]
        icon = json_obj["icon"]
        date = Date.fromisoformat(json_obj["date"])
        time = Time.fromisoformat(json_obj["time"]) if json_obj["time"] is not None else None

        return cls(
            title,
            icon,
            date,
            time,
            id
        )
    
    def update(
        self, 
        title: str | None = None,
        icon: str | None = None,
        date: Date | None = None,
        time: Time | None = None
    ):
        self.title = title if title is not None else self.title
        self.icon = icon if icon is not None else self.icon
        self.date = date if date is not None else self.date
        self.time = time if time is not None else self.time


class ReminderService(Service, Singleton):
    @Signal("changed")
    def changed(self) -> None:...

    @Property(dict, flags="readable")
    def reminders(self) -> list[Reminder]:
        return [
            Reminder.from_json_obj(id, json_obj) 
            for id, json_obj in self._reminders.items()
        ]

    def add_reminder(self, reminder: Reminder) -> None:
        """ Used to create a new reminder or update and existing reminder. """
        self._reminders[reminder.id] = reminder.to_json_obj()
        self.commit_changes()

    def delete_reminder(self, id: str) -> None:
        self._reminders.pop(id)
        self.commit_changes()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._path = None
        self._reminders: dict = None

        self._init_reminders_file()

    def is_initialized(self) -> bool:
        """ Details whether this service is in a usable state. """
        return self._path is not None and self._reminders is not None
    
    def commit_changes(self) -> None:
        self.emit("changed")
        self._write_to_disk()

    @logger.catch
    def _init_reminders_file(self):
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
    def _write_to_disk(self):
        if self.is_initialized():
            json.dump(self._reminders, self._path.open("w"))