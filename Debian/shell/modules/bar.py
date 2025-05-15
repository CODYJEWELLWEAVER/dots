from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.datetime import DateTime
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.shapes import Corner

from gi.repository import Playerctl

from util.ui import add_hover_cursor, toggle_visible

from modules.power import PowerMenu
from modules.media import Media

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
            margin='10px 20px 0px 20px',
            **kwargs
        )


        player_manager = Playerctl.PlayerManager()


        self.date_time = DateTime()
        self.power_menu = PowerMenu()
        self.media = Media(player_manager)


        self.power_menu_toggle_label = Label(
            name="power-menu-toggle-label",
            style_classes="text-icon",
            label=""
        )
        self.power_menu_toggle = Button(
            name="power-menu-toggle",
            child=self.power_menu_toggle_label,
            on_clicked=lambda *_: toggle_visible(self.power_menu)
        )


        add_hover_cursor(self.date_time)
        add_hover_cursor(self.power_menu_toggle)

        self.children = CenterBox(
            start_children=self.media,
            center_children=self.date_time,
            end_children=self.power_menu_toggle
        )