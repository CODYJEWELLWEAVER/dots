from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.box import Box

import config.icons as Icons
from util.ui import add_hover_cursor


class CreateReminder(Button):
    def __init__(self, on_clicked, **kwargs):
        super().__init__(
            name="create-reminder-button",
            child=Box(
                spacing=10,
                orientation="h",
                children=[
                    Label("Create Reminder", style_classes="create-reminder-label"),
                    Label(markup=Icons.plus, style_classes="create-reminder-icon"),
                ],
            ),
            on_clicked=on_clicked,
        )

        add_hover_cursor(self)
