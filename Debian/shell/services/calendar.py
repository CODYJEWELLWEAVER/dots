from typing import List
from fabric.core.service import Service, Property
from fabric.utils.helpers import invoke_repeater

from util.helpers import get_country_code
from util.singleton import Singleton
from config.calendar import USER_BIRTHDAY, FIRST_WEEK_DAY, UPDATE_INTERVAL

from datetime import date as Date
import calendar
from calendar import Calendar as PyCalendar
import holidays


USER_BIRTHDAY_IDENFIFIER = "User-Birthday"


class CalendarService(Service, Singleton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._country_code = get_country_code()
        self._today = Date.today()
        self._calendar = PyCalendar(firstweekday=FIRST_WEEK_DAY)
        self._selected_date = self._today
        self._holidays = holidays.country_holidays(self._country_code)
        self._user_birthday = Date.fromisoformat(USER_BIRTHDAY)

        # TODO: Find a more efficient way to check this?
        # check every minute for change of date
        invoke_repeater(UPDATE_INTERVAL, self.update_today)  # 60 seconds

    @Property(Date, flags="readable")
    def today(self) -> Date:
        return self._today

    @Property(Date, flags="read-write")
    def selected_date(self) -> Date:
        return self._selected_date

    @selected_date.setter
    def selected_date(self, new_date: Date) -> None:
        self._selected_date = new_date

    @Property(List[Date], flags="readable")
    def month_calendar(self) -> List[Date]:
        return [
            date
            for date in self._calendar.itermonthdates(
                self.selected_date.year, self.selected_date.month
            )
        ]

    @Property(str, flags="readable")
    def current_month(self) -> str:
        return self.get_month_name(self.today.month)

    @Property(str, flags="readable")
    def selected_day(self) -> str:
        suffix = self.get_ordinal_suffix(self.selected_date.day)
        return str(self.selected_date.day) + suffix

    @Property(str, flags="readable")
    def selected_month(self) -> str:
        return self.get_month_name(self.selected_date.month)

    @Property(str, flags="readable")
    def selected_year(self) -> str:
        return str(self.selected_date.year)

    @Property(List[str], flags="readable")
    def holidays(self) -> list[str]:
        date = self.selected_date
        holidays = []

        if date in self._holidays:
            holidays.append(self._holidays[date])

        if (
            date.month == self._user_birthday.month
            and date.day == self._user_birthday.day
        ):
            user_age = date.year - self._user_birthday.year
            suffix = self.get_ordinal_suffix(user_age)
            holidays.append(f"{USER_BIRTHDAY_IDENFIFIER} {user_age}{suffix}")

        return holidays

    def get_month_name(self, month: int) -> str:
        return calendar.month_name[month]

    def get_ordinal_suffix(self, day: int):
        if day == 1:
            return "st"
        elif day == 2:
            return "nd"
        elif day == 3:
            return "rd"
        else:
            return "th"

    def update_today(self) -> bool:
        today = Date.today()

        if today != self.today:
            self._today = today
            self.notify("today")

        return True

    def select_prev_month(self) -> None:
        selected_month = self.selected_date.month
        selected_year = self.selected_date.year

        prev_month = selected_month - 1 if selected_month > 1 else 12
        year = selected_year if prev_month != 12 else selected_year - 1

        self.selected_date = Date(year, prev_month, 1)

    def select_next_month(self) -> None:
        selected_month = self.selected_date.month
        selected_year = self.selected_date.year

        next_month = selected_month + 1 if selected_month < 12 else 1
        year = selected_year if next_month != 1 else selected_year + 1

        self.selected_date = Date(year, next_month, 1)

    def select_prev_year(self) -> None:
        year = self.selected_date.year - 1
        day = self.today.day if year == self.today.year else 1
        month = self.today.month if year == self.today.year else 1
        # if jumping to current year, select today, else select first day of year
        self.selected_date = Date(year, month, day)

    def select_next_year(self) -> None:
        year = self.selected_date.year + 1
        day = self.today.day if year == self.today.year else 1
        month = self.today.month if year == self.today.year else 1
        # if jumping to current year, select today, else select first day of year
        self.selected_date = Date(year, month, day)

    def select_prev_day(self) -> None:
        calendar = self.month_calendar
        selected_date_idx = calendar.index(self.selected_date)
        prev_day = calendar[selected_date_idx - 1]
        self.selected_date = prev_day

    def select_next_day(self) -> None:
        calendar = self.month_calendar
        selected_date_idx = calendar.index(self.selected_date)
        next_day = calendar[selected_date_idx + 1]
        self.selected_date = next_day

    def select_month(self, month: int) -> None:
        year = self.selected_date.year
        self.selected_date = Date(year, month, 1)

    def select_day(self, day: int) -> None:
        prev_date = self.selected_date
        self.selected_date = Date(prev_date.year, prev_date.month, day)
