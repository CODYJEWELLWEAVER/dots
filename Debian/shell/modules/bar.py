from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.datetime import DateTime
from fabric.widgets.eventbox import EventBox
from fabric.widgets.box import Box
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.shapes.corner import Corner
from fabric.hyprland.widgets import WorkspaceButton, Workspaces

from modules.media import MediaControl
from modules.power import PowerControl

from util.ui import add_hover_cursor

from gi.repository import Playerctl

"""
Status bar for shell.
"""

class Bar(Window):
    def __init__(self, control_panel, **kwargs):
        super().__init__(
            name="bar",
            layer="top",
            anchor="left top right",
            exclusivity="auto",
            **kwargs
        )


        self.control_panel = control_panel


        self.player_manager = Playerctl.PlayerManager()
        self.media = MediaControl(self.player_manager)


        self.power = PowerControl()


        self.workspaces = Workspaces(
            name="workspaces",
            buttons=[
                WorkspaceButton(workspace_id)
                for workspace_id in range(1, 10)
            ]
        )


        self.date_time = DateTime(
            name="date-time",
        )
        add_hover_cursor(self.date_time)


        self.control_panel_expander = EventBox(
            events="enter-notify",
            child=Box(
                name="expander-box",
                children=[
                    Corner(
                        orientation="top-right",
                        name="left-corner",
                        size=(75, 25)
                    ),
                    self.date_time,
                    Corner(
                        orientation="top-left",
                        name="right-corner",
                        size=(75, 25)
                    )
                ]
            )
        )


        self.control_panel_expander.connect("enter-notify-event", self.show_control_panel)


        self.children = CenterBox(
            v_align="center",
            start_children=self.media,
            center_children=self.control_panel_expander,
            end_children=[
                self.workspaces,
                self.power
            ]
        )


    def show_control_panel(self, *args):
        self.control_panel.show()