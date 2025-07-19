from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.datetime import DateTime
from fabric.widgets.eventbox import EventBox
from fabric.widgets.box import Box
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.shapes.corner import Corner
from fabric.hyprland.widgets import WorkspaceButton, Workspaces

from modules.control_panel import ControlPanel
from modules.media import MediaControl
from modules.power import PowerControl
from modules.sys_info import CPUUsage, GPUUsage, RAM, Disk, NetworkInfo
from modules.weather import WeatherInfo
from util.ui import corner


from gi.repository import Playerctl


"""
Status bar for shell.
"""


class Bar(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="bar",
            layer="overlay",
            anchor="left top right",
            exclusivity="auto",
            **kwargs,
        )

        self.control_panel = ControlPanel.get_instance()

        self.player_manager = Playerctl.PlayerManager()
        
        self.media = MediaControl(self.player_manager)

        self.power = PowerControl()

        self.weather_info = WeatherInfo(size="small")

        self.cpu_usage = CPUUsage()
        self.gpu_usage = GPUUsage()
        self.ram = RAM()
        self.disk = Disk()
        self.network = NetworkInfo()

        self.workspaces = Workspaces(
            name="workspaces",
            buttons=[WorkspaceButton(workspace_id) for workspace_id in range(1, 11)],
        )

        self.date_time = DateTime(
            formatters="%I:%M %p",
            name="date-time",
        )

        # event box to expand control panel
        self.control_panel_expander = EventBox(
            events="enter-notify",
            child=Box(
                name="expander-box",
                children=[
                    corner("left", "small"),
                    self.date_time,
                    corner("right", "small"),
                ],
            ),
        )

        self.control_panel_expander.connect(
            "enter-notify-event", self.show_control_panel
        )

        self.children = CenterBox(
            v_align="center",
            start_children=[self.workspaces, self.media],
            center_children=self.control_panel_expander,
            end_children=[
                self.weather_info,
                self.cpu_usage,
                self.gpu_usage,
                self.ram,
                self.disk,
                self.network,
                self.power,
            ],
        )

    def show_control_panel(self, *args):
        self.control_panel.show()
