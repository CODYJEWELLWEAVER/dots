from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.shapes.corner import Corner
from fabric.widgets.datetime import DateTime
from fabric.widgets.stack import Stack

from modules.weather import WeatherInfo
from modules.calendar import Calendar
from widgets.custom_image import CustomImage
from config.profile import PROFILE_IMAGE_PATH
from util.helpers import get_system_node_name, get_user_login_name
from util.singleton import Singleton
from modules.network import NetworkOverview, ConnectionSettings
from modules.notifications import NotificationsOverview
from services.reminders import ReminderService
from modules.reminders import CreateReminderView

from gi.repository import GdkPixbuf

# TODO: Fix some small issues with the content stack and how the animations look


class ControlPanel(Window, Singleton):
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

        self.reminder_service = ReminderService.get_instance()

        self.network_overview = NetworkOverview(self.show_connections_view)
        self.connection_settings = ConnectionSettings(self.show_main_view)

        self.notifications_overview = NotificationsOverview(
            on_switch=self.show_to_do_list
        )

        self.profile_image = Box(
            name="profile-image-box",
            h_align="center",
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

        self.weather_info = WeatherInfo(size="large")

        self.profile_box = Box(
            orientation="v",
            spacing=20,
            h_align="center",
            v_align="center",
            children=[
                self.profile_image,
                self.system_name,
                self.datetime,
                self.weather_info,
            ],
        )

        self.calendar = Calendar(
            show_reminder_creation_view=self.show_reminder_creation_view
        )

        self.create_reminder = CreateReminderView(on_close=self.show_main_view)

        self.productivity_stack = Stack(
            transition_duration=400,
            transition_type='over-left-right',
            name="productivity-stack",
            children=[
                self.notifications_overview
            ]
        )

        self.productivity_stack.set_hhomogeneous(True)
        self.productivity_stack.set_vhomogeneous(True)

        self.top_row = Box(
            orientation="h",
            spacing=40,
            children=[
                self.profile_box,
                self.calendar,
                self.productivity_stack,
            ],
        )

        self.bottom_row = Box(
            spacing=20,
            orientation="h",
            h_align="start",
            children=[
                self.network_overview,
            ],
        )

        self.main_view = Box(
            orientation="h",
            children=[
                self.left_corner(),
                Box(
                    style_classes="view-box",
                    spacing=40,
                    orientation="v",
                    children=[
                        self.top_row,
                        self.bottom_row,
                    ],
                ),
                self.right_corner(),
            ],
        )

        self.connections_view = Box(
            orientation="h",
            children=[
                self.left_corner(),
                self.connection_settings,
                self.right_corner(),
            ],
        )

        self.create_reminder_view = Box(
            orientation="h",
            children=[
                self.left_corner(),
                self.create_reminder,
                self.right_corner(),
            ],
        )

        self.main_content_stack = Stack(
            transition_type="over-down-up",
            transition_duration=250,
            interpolate_size=True,
            h_expand=True,
            v_expand=True,
            children=[self.main_view, self.connections_view, self.create_reminder_view],
        )

        # allow stack to grow and shrink with each child
        self.main_content_stack.set_hhomogeneous(False)

        self.show_main_view()

        self.children = self.main_content_stack

        self.connect("focus-out-event", lambda *_: self.hide())

    def left_corner(self) -> Box:
        return Box(
            style_classes="corner-box",
            children=Corner("top-right", style_classes="left-corner", size=(225, 75)),
        )

    def right_corner(self) -> Box:
        return Box(
            style_classes="corner-box",
            children=Corner("top-left", style_classes="right-corner", size=(225, 75)),
        )

    def show_main_view(self, *args):
        self.main_content_stack.set_visible_child(self.main_view)

    def show_connections_view(self, *args):
        self.main_content_stack.set_visible_child(self.connections_view)

    def show_reminder_creation_view(self, *args):
        self.create_reminder.set_date()
        self.main_content_stack.set_visible_child(self.create_reminder_view)

    def show_to_do_list(self, *args):
        pass


class ProfileImage(CustomImage):
    def __init__(self, width, height, **kwargs):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            PROFILE_IMAGE_PATH, width, height, True
        )

        super().__init__(
            name="profile-image",
            pixbuf=pixbuf,
            **kwargs,
        )
