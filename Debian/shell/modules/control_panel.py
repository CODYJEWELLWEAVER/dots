from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.eventbox import EventBox
from fabric.widgets.shapes.corner import Corner
from fabric.widgets.datetime import DateTime

from services.weather import WeatherService
from modules.weather import WeatherInfo
from widgets.custom_image import CustomImage
from config.profile import PROFILE_IMAGE_PATH
from util.helpers import get_system_node_name, get_user_login_name

from gi.repository import GdkPixbuf


class ControlPanel(Window):
    def __init__(self, weather_service: WeatherService, **kwargs):
        super().__init__(
            layer="overlay",
            title="fabric-control-panel",
            name="control-panel",
            anchor="top center",
            exclusivity="none",
            margin="-60px 0px 0px 0px",
            visible=False,
            kwargs=kwargs    
        )


        self.profile_image = Box(
            name="profile-image-box",
            children=ProfileImage(200, 200),
            h_expand=True,
            v_expand=True
        )


        self.system_name = Label(
            name="system-name",
            label=f"{get_user_login_name()}@{get_system_node_name()}"
        )

        
        self.datetime = DateTime(
            formatters="%I:%M %p",
            name="control-panel-time",
        )

        
        # TODO: Add specific weather widget for control panel with
        # forecast and more information.
        self.weather_info = WeatherInfo(weather_service, bar=False)


        self.content_box = Box(
            children=[
                Corner(
                    "top-right",
                    name="control-panel-left-corner",
                    size=(225, 75)
                ),
                Box(
                    name="control-panel-box",
                    orientation="v",
                    children=[
                        Box(
                            spacing = 10,
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
                                        self.weather_info
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                Corner(
                    "top-left",
                    name="control-panel-left-corner",
                    size=(225, 75)
                ),
            ]
        )


        self.event_box = EventBox(
            events="leave-notify",
            child=self.content_box,
            name="control-panel-event-box",
            h_expand=True,
            v_expand=True
        )


        self.event_box.connect("leave-notify-event", lambda *_: self.hide())


        self.children = self.event_box


class ProfileImage(CustomImage):
    def __init__(self, width, height, **kwargs):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            PROFILE_IMAGE_PATH,
            width,
            height,
            True
        )

        super().__init__(
            name="profile-image",
            pixbuf=pixbuf,
        )