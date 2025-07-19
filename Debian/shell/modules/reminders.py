from typing import Callable
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.box import Box
from fabric.widgets.entry import Entry

import config.icons as Icons
from services.calendar import CalendarService
from services.reminders import ReminderService, Reminder
from util.ui import add_hover_cursor, toggle_visible

from datetime import time as Time


class CreateReminderButton(Button):
    def __init__(self, on_clicked: Callable, **kwargs):
        super().__init__(
            name="create-reminder-button",
            child=Box(
                spacing=10,
                orientation="h",
                h_align="center",
                children=[
                    Label("Create Reminder", style_classes="create-reminder-label"),
                    Label(markup=Icons.plus, style_classes="create-reminder-icon"),
                ],
            ),
            on_clicked=on_clicked,
            **kwargs
        )

        add_hover_cursor(self)


class CreateReminderView(Box):
    def __init__(self, on_close: Callable, **kwargs):
        super().__init__(
            name="create-reminder-view",
            style_classes="view-box",
            spacing=20,
            orientation="h",
            **kwargs,
        )

        self.on_close = on_close

        self.date_label = Label()

        self.title_entry = Entry(
            name="create-reminder-title-entry",
            placeholder="Reminder Title",
            h_align="center",
            h_expand=True,
        )

        self.all_day_button_label = Label("All Day")
        self.all_day_button = Button(
            name="create-reminder-all-day-button",
            child=self.all_day_button_label,
            on_clicked=self.on_all_day_changed,
            h_align="center",
        )
        add_hover_cursor(self.all_day_button)

        self.time_selection = TimeSelection(visible=False)

        self.create_button = Button(
            name="confirm-create-reminder-button",
            style_classes="confirm-create-reminder-button-disabled",
            child=Label("Create Reminder"),
            on_clicked=self.create_reminder,
        )
        self.create_button.set_sensitive(False)
        add_hover_cursor(self.create_button)

        self.add(
            Box(
                spacing=40,
                orientation="v",
                v_align="center",
                children=[
                    self.date_label,
                    self.title_entry,
                    self.all_day_button,
                    self.time_selection,
                    self.create_button,
                ],
            )
        )

        back_button = Button(
            child=Label(markup=Icons.arrow_right),
            on_clicked=self.close,
        )
        add_hover_cursor(back_button)

        self.add(back_button)

        self.calendar_service = CalendarService.get_instance()

        self.reminder_service = ReminderService.get_instance()

        self.title_entry.connect("notify::text", self.on_title_changed)

    def create_reminder(self, *args):
        title = self.title_entry.get_text()
        date = self.calendar_service.selected_date
        time = (
            self.time_selection.get_time() if self.time_selection.is_visible() else None
        )

        reminder = Reminder(title, date, time)
        self.reminder_service.add_reminder(reminder)

        self.close()

    def reset(self):
        self.title_entry.set_text("")
        self.time_selection.set_visible(False)
        self.time_selection.hour = Label(
            label="12",
        )
        self.time_selection.minute = Label(label="00")
        self.time_selection.am_pm_label = Label("PM")

    def close(self, *args):
        self.on_close()
        self.reset()

    def set_date(self):
        self.date_label.set_property("label", f"Reminder for: {self.get_date_text()}")

    def get_date_text(self):
        return (
            self.calendar_service.selected_month
            + " "
            + self.calendar_service.selected_day
            + " "
            + self.calendar_service.selected_year
        )

    def on_all_day_changed(self, *args):
        if not self.time_selection.is_visible():
            label = "Specific Time"
        else:
            label = "All Day"

        toggle_visible(self.time_selection)

        self.all_day_button_label.set_property("label", label)

    def on_title_changed(self, *args):
        title = self.title_entry.get_text()
        if title is None or title == "":
            enabled = False
        else:
            enabled = True
        self.create_button.set_sensitive(enabled)


class TimeSelection(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="create-reminder-time-selection",
            spacing=20,
            orientation="h",
            h_align="center",
            **kwargs,
        )

        self.hour = Label(
            label="12",
        )
        self.increase_hour_button = self.arrow_up_button(self.increment_hour)
        self.decrease_hour_button = self.arrow_down_button(self.decrement_hour)
        add_hover_cursor(self.increase_hour_button)
        add_hover_cursor(self.decrease_hour_button)

        hour_selector = Box(
            spacing=10,
            orientation="v",
            children=[self.increase_hour_button, self.hour, self.decrease_hour_button],
        )

        self.minute = Label(
            label="00",
        )
        self.increase_minute_button = self.arrow_up_button(self.increment_minute)
        self.decrease_minute_button = self.arrow_down_button(self.decrement_minute)
        add_hover_cursor(self.increase_minute_button)
        add_hover_cursor(self.decrease_minute_button)

        minute_selector = Box(
            spacing=10,
            orientation="v",
            children=[
                self.increase_minute_button,
                self.minute,
                self.decrease_minute_button,
            ],
        )

        self.am_pm_label = Label("PM")
        am_pm_selector = Button(
            name="am-pm-selector-button",
            child=self.am_pm_label,
            on_clicked=self.toggle_am_pm,
        )
        add_hover_cursor(am_pm_selector)

        self.add(Label("Hour:"))
        self.add(hour_selector)
        self.add(Label("Minute:"))
        self.add(minute_selector)
        self.add(am_pm_selector)

    def get_time(self) -> Time:
        hour = self.get_hour()
        if hour != 12 and self.is_pm_selected():
            hour += 12

        return Time(hour, self.get_minute())

    def get_hour(self) -> int:
        return int(self.hour.get_property("label"))

    def set_hour(self, new_hour: int):
        label = str(new_hour) if new_hour >= 10 else "0" + str(new_hour)
        self.hour.set_property("label", label)

    def get_minute(self) -> int:
        return int(self.minute.get_property("label"))

    def set_minute(self, new_minute: int):
        label = str(new_minute) if new_minute >= 10 else "0" + str(new_minute)
        self.minute.set_property("label", label)

    def is_pm_selected(self) -> bool:
        return self.am_pm_label.get_property("label") == "PM"

    def increment_hour(self, *args):
        hour = self.get_hour()
        new_hour = (hour % 12) + 1
        self.set_hour(new_hour)

    def decrement_hour(self, *args):
        hour = self.get_hour()
        new_hour = hour - 1 if hour != 1 else 12
        self.set_hour(new_hour)

    def increment_minute(self, *args):
        minute = self.get_minute()
        new_minute = (minute + 1) % 60
        self.set_minute(new_minute)

    def decrement_minute(self, *args):
        minute = self.get_minute()
        new_minute = (minute - 1) % 60
        self.set_minute(new_minute)

    def toggle_am_pm(self, *args):
        if self.is_pm_selected():
            label = "AM"
        else:
            label = "PM"
        self.am_pm_label.set_property("label", label)

    def arrow_up_button(self, on_clicked: Callable) -> Button:
        return Button(
            child=Label(style_classes="create-reminder-icon", markup=Icons.arrow_up),
            on_clicked=on_clicked,
        )

    def arrow_down_button(self, on_clicked: Callable) -> Button:
        return Button(
            child=Label(style_classes="create-reminder-icon", markup=Icons.arrow_down),
            on_clicked=on_clicked,
        )
