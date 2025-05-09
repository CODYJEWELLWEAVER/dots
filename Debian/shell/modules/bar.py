from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.datetime import DateTime
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.button import Button
from fabric.widgets.label import Label

from util.ui import add_hover_cursor, toggle_visibility

from modules.power import PowerMenu
from gi.repository import Gdk

"""
Status bar for shell.
"""

class Bar(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="bar",
            layer="top",
            anchor="left top right",
            exclusivity="auto",
            margin='20px 20px 0px 20px',
            **kwargs
        )

        self.date_time = DateTime()
        self.power_menu = PowerMenu()

        # Toggle power menu
        self.power_menu_toggle_label = Label(
            name="power-menu-toggle-label",
            label=""
        )
        self.power_menu_toggle = Button(
            name="power-menu-toggle",
            child=self.power_menu_toggle_label,
            on_clicked=lambda *_: toggle_visibility(self.power_menu)
        )

        add_hover_cursor(self.date_time)
        add_hover_cursor(self.power_menu_toggle)

        self.children = CenterBox(
            center_children=self.date_time,
            end_children=self.power_menu_toggle,
        )