from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.shapes.corner import Corner
from fabric.widgets.datetime import DateTime

from modules.weather import WeatherInfo
from modules.calendar import Calendar
from widgets.custom_image import CustomImage
from config.profile import PROFILE_IMAGE_PATH
from util.helpers import get_system_node_name, get_user_login_name

from gi.repository import GdkPixbuf


class ControlPanel(Window):
    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            title="fabric-control-panel",
            name="control-panel",
            anchor="top center",
            exclusivity="none",
            margin="-62px 0px 0px 0px",
            visible=False,
            keyboard_mode="on-demand",
            kwargs=kwargs,
        )

        self.profile_image = Box(
            name="profile-image-box",
            children=ProfileImage(200, 200),
        )

        self.system_name = Label(
            name="system-name",
            label=f"{get_user_login_name()}@{get_system_node_name()}",
        )

        self.datetime = DateTime(
            formatters="%I:%M %p",
            name="control-panel-time",
        )

        # TODO: Add specific weather widget for control panel with
        # forecast and more information.
        self.weather_info = WeatherInfo(bar=False)

        self.calendar = Calendar()

        self.connect("focus-out-event", lambda *_: self.hide())

        self.children = Box(
            children=[
                Box(
                    style_classes="corner-box",
                    children=Corner("top-right", name="left-corner", size=(225, 75)),
                ),
                Box(
                    name="control-panel-box",
                    orientation="v",
                    children=[
                        Box(
                            spacing=40,
                            orientation="h",
                            children=[
                                Box(
                                    orientation="v",
                                    spacing=20,
                                    h_align="center",
                                    children=[
                                        self.profile_image,
                                        self.system_name,
                                        self.datetime,
                                        self.weather_info,
                                    ],
                                ),
                                Box(
                                    orientation="v",
                                    spacing=20,
                                    h_align="center",
                                    children=[self.calendar],
                                ),
                            ],
                        )
                    ],
                ),
                Box(
                    style_classes="corner-box",
                    children=Corner("top-left", name="right-corner", size=(225, 75)),
                ),
            ]
        )


class ProfileImage(CustomImage):
    def __init__(self, width, height, **kwargs):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            PROFILE_IMAGE_PATH, width, height, True
        )

        super().__init__(
            name="profile-image",
            pixbuf=pixbuf,
        )
