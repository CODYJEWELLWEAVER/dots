from typing import Iterable
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button

from datetime import date
from services.calendar import Calendar as CalendarService


class Calendar(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="calendar",
            orientation="v",
            spacing=10,
            h_align="center",
            **kwargs
        )


        self.calendar_service = CalendarService.get_instance()


        self.weeks = self.get_weeks()   


        self.month_label = Label(
            name="month-label",
            label=self.calendar_service.month_name
        )


        self.calendar = Box(
            orientation='v',
            spacing=10,
            children=self.weeks
        )


        self.children = [
            self.month_label,
            self.calendar
        ]


    def get_weeks(self) -> Iterable[Box]:
        month_calendar = self.calendar_service.month_calendar
        weeks = []

        for i in range(0, len(month_calendar), 7):
            weeks.append(
                Box(
                    spacing=2,
                    children=[
                        DayButton(date)
                        for date
                        in month_calendar[i:min(i+7,len(month_calendar))]
                    ]
                )
            )

        return weeks
    

class DayButton(Button):
    def __init__(self, date, **kwargs):
        super().__init__(
            style_classes="day-button",
            child=Label(
                str(date.day),
                style_classes="day-label"
            ),
            **kwargs
        )