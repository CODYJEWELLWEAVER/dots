from typing import Iterable
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button

from services.calendar import Calendar as CalendarService

import config.icons as icons
from util.ui import add_hover_cursor, toggle_visible


class Calendar(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="calendar",
            orientation="v",
            spacing=10,
            h_expand=True,
            h_align="center",
            v_align="center",
            **kwargs
        )


        self.service = CalendarService.get_instance()  


        self.day_label = Label(
            name="day-label",
            label=self.service.selected_day,
            visible=False
        )


        self.month_label = Label(
            name="month-label",
            label=self.service.selected_month
        )


        self.year_label = Label(
            name="year-label",
            label=self.service.selected_year
        )


        self.prev_month = Button(
            style_classes="month-skip-button",
            child=Label(
                markup=icons.arrow_left,
            ),
            on_clicked=self.do_select_prev
        )
        add_hover_cursor(self.prev_month)


        self.next_month = Button(
            style_classes="month-skip-button",
            child=Label(
                markup=icons.arrow_right,
            ),
            on_clicked=self.do_select_next
        )
        add_hover_cursor(self.next_month)


        self.calendar_swap_button = Button(
            name="calendar-swap-button",
            child=Box(
                spacing=10,
                h_align="center",
                children=[
                    self.month_label,
                    self.day_label,
                    self.year_label
                ]
            ),
            on_clicked=self.do_swap_calendar
        )
        add_hover_cursor(self.calendar_swap_button)


        self.day_calendar = Box(
            orientation='v',
            spacing=2,
            h_align="center",
            children=self.get_day_buttons(),
            visible=True
        )


        self.month_calendar = Box(
            orientation='v',
            spacing=2,
            h_align="center",
            children=self.get_month_buttons(),
            visible=False
        )


        self.day_view = Box(
            name="day-view",
            h_align="center",
            h_expand=True,
            v_expand=True,
            orientation="v",
            children=[
            ],
            visible=False
        )


        self.children = [
            Box(
                h_align="fill",
                spacing=10,
                children=[
                    self.prev_month,
                    Box(
                        h_expand=True,
                        h_align="center",
                        children=[
                            self.calendar_swap_button,
                        ],
                    ),
                    self.next_month
                ]
            ),
            self.day_calendar,
            self.month_calendar,
            self.day_view
        ]


        self.service.connect(
            "notify::selected-date",
            self.on_selected_date_changed
        )


    def get_day_buttons(self) -> Iterable[Box]:
        month_calendar = self.service.month_calendar
        weeks = []

        for i in range(0, len(month_calendar), 7):
            weeks.append( # get day buttons organized by weeks
                Box(
                    spacing=2,
                    children=[
                        DayButton(
                            day=date.day,
                            in_cur_month=date.month == self.service.selected_date.month,
                            name="today" if date == self.service.today else "",
                            on_clicked=lambda b, date=date: 
                                self.do_select_day(date)
                        )
                        for date
                        in month_calendar[i:min(i+7,len(month_calendar))]
                    ]
                )
            )

        return weeks
    

    # TODO: Tidy this a bit
    def get_month_buttons(self, num_cols=3) -> Iterable[Box]:
        current_month = self.service.current_month
        selected_year = self.service.selected_date.year
        current_year = self.service.today.year
        month_names = [
            self.service.get_month_name(month)
            for month in range(1, 13)
        ]
        month_enum = [(idx, month) for (idx, month) in enumerate(month_names, start=1)]
        months = []

        for i in range(0, 12, num_cols):
            months.append(
                Box(
                    spacing=10,
                    h_align="center",
                    h_expand=True,
                    children=[
                        MonthButton(
                            month_name=month,
                            name="current-month" if month == current_month
                            and current_year == selected_year else "",
                            on_clicked=lambda b, idx=idx: self.do_select_month(idx)
                        )
                        for (idx, month) in month_enum[i: i+num_cols]
                    ]
                )
            )

        return months
    

    def do_select_prev(self, button):
        if self.day_calendar.is_visible():
            self.service.select_prev_month()
        else:
            self.service.select_prev_year()


    def do_select_next(self, button):
        if self.day_calendar.is_visible():
            self.service.select_next_month()
        else:
            self.service.select_next_year()


    def do_select_month(self, month):
        self.service.select_month(month)
        self.do_swap_calendar()


    def do_select_day(self, date):
        self.service.selected_date = date
        toggle_visible(self.day_label)
        toggle_visible(self.day_calendar)
        toggle_visible(self.day_view)


    def do_swap_calendar(self, *args):
        if self.day_view.is_visible():
            toggle_visible(self.day_calendar)
            toggle_visible(self.day_view)
            toggle_visible(self.day_label)
        else:
            toggle_visible(self.day_calendar)
            toggle_visible(self.month_calendar)
            toggle_visible(self.month_label)
    

    def on_selected_date_changed(self, service: CalendarService, _):
        self.day_calendar.children = self.get_day_buttons()
        self.month_calendar.children = self.get_month_buttons()
        self.month_label.set_property("label", service.selected_month)
        self.year_label.set_property("label", service.selected_year)
        self.day_label.set_property("label", service.selected_day)
    

class DayButton(Button):
    def __init__(self, day: int, in_cur_month: bool, **kwargs):
        super().__init__(
            style_classes="day-button",
            child=Label(
                label=str(day),
                style_classes="day-button-label" if in_cur_month 
                else "alt-day-button-label"
            ),
            **kwargs
        )


class MonthButton(Button):
    def __init__(self, month_name: str, **kwargs):
        super().__init__(
            style_classes="month-button",
            child=Label(
                label=month_name,
                style_classes="month-button-label"
            ),
            **kwargs
        )