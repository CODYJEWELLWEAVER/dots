from typing import Iterable
from fabric.core.service import Service, Property, Signal
from fabric.utils.helpers import invoke_repeater

from util.helpers import get_country_code
from util.singleton import Singleton

from datetime import date as Date
import calendar
from calendar import Calendar as PyCalendar
import holidays


class Calendar(Service, Singleton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


        self._country_code = get_country_code()
        self._today = Date.today()
        self._calendar = PyCalendar(firstweekday=6)
        self._selected_date = self._today
        self._holidays = holidays.country_holidays(self._country_code)


        # TODO: Find a more efficient way to check this?
        # check every minute for change of date
        invoke_repeater(60000, self.poll_for_date_change) # 60 seconds


    @Property(Date, flags="readable")
    def today(self) -> Date:
        return self._today
    

    @today.setter
    def today(self, new_date: Date) -> None:
        self._today = new_date


    @Property(Date, flags="read-write")
    def selected_date(self) -> Date:
        return self._selected_date
    

    @selected_date.setter
    def selected_date(self, new_date: Date) -> None:
        self._selected_date = new_date


    @Property(Iterable[Date], flags="readable")
    def month_calendar(self) -> Iterable[Date]:
        return [date for date in self._calendar.itermonthdates(
            self.selected_date.year, self.selected_date.month)]
    

    @Property(str, flags="readable")
    def month_name(self) -> str:
        return calendar.month_name[self.selected_date.month]


    def get_holiday(self, date: Date) -> str | None:
        if date in self._holidays:
            return self._holidays[Date]
        else:
            return None
        

    def poll_for_date_change(self) -> bool:
        today = Date.today()

        if today != self.today:
            self.today = today

        return True