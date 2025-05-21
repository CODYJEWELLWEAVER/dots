from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.datetime import DateTime

from util.ui import add_hover_cursor

"""
Status bar for shell.
"""

class StatusBar(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="bar",
            layer="top",
            anchor="top center",
            exclusivity="auto",
            margin='10px 0px 0px 0px',
            **kwargs
        )


        self.date_time = DateTime(
            name="date-time"
        )


        add_hover_cursor(self.date_time)


        self.children = self.date_time