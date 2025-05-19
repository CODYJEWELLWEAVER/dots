from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.datetime import DateTime
from fabric.widgets.button import Button
from fabric.widgets.label import Label

from util.ui import add_hover_cursor, toggle_visible
from util.helpers import get_icon_pixbuff
from util.icons import ICONS

from modules.power import PowerMenu
from modules.media import Media

"""
Status bar for shell.
"""

class StatusBar(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="bar",
            layer="overlay",
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