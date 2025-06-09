from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scrolledwindow import ScrolledWindow

from fabric.utils.helpers import truncate, bulk_connect

from services.network import NetworkService
import config.icons as icons
from util.ui import add_hover_cursor

import gi
from gi.repository import NM

gi.require_version("NM", "1.0")


WIFI_ENABLED_LABEL = "On"
WIFI_DISABLED_LABEL = "Off"


def get_connection_id(connection: NM.ActiveConnection) -> str:
    if connection is not None:
        return truncate(connection.get_id(), 18)
    else:
        return "Disconnected"

def get_connection_icon(connection: NM.ActiveConnection | NM.RemoteConnection):
    return (
        icons.wifi if "wireless" in connection.get_connection_type() else icons.ethernet
    )

def get_strength_icon(strength: int) -> str:
    if strength >= 80:
        return icons.wifi_signal_strong
    elif strength >= 60:
        return icons.wifi_signal_good
    elif strength >= 40:
        return icons.wifi_signal_fair
    else:
        return icons.wifi_signal_weak


class NetworkControl(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="network-control",
            orientation="v",
            h_align="center",
            h_expand=True,
            **kwargs,
        )

        self.connection_settings = ConnectionSettings()

        self.network_service = NetworkService.get_instance()
        self._active_wifi_connection = self.network_service.wifi_connection

        # Toggle Wireless Control
        self.toggle_wifi_icon = Label(
            style_classes="network-control-icon", markup=icons.wifi
        )
        self.toggle_wifi_label = Label(
            style_classes="network-control-label",
            label=WIFI_ENABLED_LABEL
            if self.network_service.wifi_enabled
            else WIFI_DISABLED_LABEL,
        )
        self.toggle_wifi_child_box = Box(
            spacing=10,
            orientation="h",
            children=[self.toggle_wifi_icon, self.toggle_wifi_label],
        )
        self.toggle_wifi = Button(
            style_classes="network-control-button",
            child=self.toggle_wifi_child_box,
            on_clicked=self.do_toggle_wifi,
        )
        add_hover_cursor(self.toggle_wifi)

        # Control for wifi networks
        self.wifi_connection_label = Label(
            style_classes="network-control-label",
            label=get_connection_id(self._active_wifi_connection),
        )
        self.wifi_status_icon = Label(
            style_classes="network-control-icon", markup=icons.link
        )
        self.wifi_child_box = Box(
            spacing=10,
            orientation="h",
            children=[
                self.wifi_connection_label,
                self.wifi_status_icon,
            ],
        )
        self.wifi = Button(
            style_classes="network-control-button",
            h_expand=True,
            h_align="center",
            child=self.wifi_child_box,
            on_clicked=self.do_show_connection_settings,
        )
        add_hover_cursor(self.wifi)

        self.children = [
            Box(
                spacing=10,
                orientation="h",
                h_expand=True,
                h_align="fill",
                children=[self.toggle_wifi, self.wifi],
            )
        ]

        bulk_connect(
            self.network_service,
            {
                "notify::wifi-connection": self.on_wifi_connection_changed,
                "notify::wifi-enabled": self.on_wifi_enabled_changed,
            },
        )

    def do_toggle_wifi(self, *args):
        self.network_service.toggle_wireless()

    def on_wifi_enabled_changed(self, service, _):
        wifi_enabled = service.wifi_enabled
        self.toggle_wifi_icon = Label(
            style_classes="network-control-icon",
            markup=icons.wifi if wifi_enabled else icons.wifi_off,
        )
        self.toggle_wifi_label.set_property(
            "label", WIFI_ENABLED_LABEL if wifi_enabled else WIFI_DISABLED_LABEL
        )
        self.toggle_wifi_child_box.children = [
            self.toggle_wifi_icon,
            self.toggle_wifi_label,
        ]

    def on_wifi_connection_changed(self, service, _):
        self._active_wifi_connection = service.wifi_connection
        self.wifi_connection_label.set_property(
            "label", get_connection_id(self._active_wifi_connection)
        )

        if self._active_wifi_connection is None:
            status_icon = icons.link_off
        else:
            status_icon = icons.link
        self.wifi_status_icon = Label(
            style_classes="network-control-icon", markup=status_icon
        )

        self.wifi_child_box.children = [
            self.wifi_connection_label,
            self.wifi_status_icon,
        ]

    def do_show_connection_settings(self, *args):
        self.connection_settings.show_all()


class ConnectionSettings(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="connection-settings",
            layer="top",
            anchor="center",
            exclusivity="none",
            visible=False,
            **kwargs,
        )

        self.network_service = NetworkService.get_instance()

        self.connections_box = Box(
            name="connections-box",
            orientation="v",
            h_expand=True,
            spacing=10,
            children=self.get_connection_elements(),
        )
        self.connections_view = ScrolledWindow(
            name="connections-view",
            child=self.connections_box
        )

        self.access_points_box = Box(
            name="access-points-box",
            orientation="v",
            spacing=10,
            children=self.get_access_point_elements(),
        )
        self.access_points_view = ScrolledWindow(
            name="access-points-view",
            child=self.access_points_box
        )

        self.content_box = Box(
            name="connection-settings-content",
            orientation="h",
            spacing=40,
            h_align="center",
            v_align="center",
            v_expand=True,
            children=[
                Box(
                    orientation="v",
                    spacing=10,
                    v_expand=True,
                    h_expand=True,
                    children=[
                        Label("Saved Connections"),
                        self.connections_view
                    ],
                ),
                Box(
                    orientation="v",
                    spacing=10,
                    v_expand=True,
                    h_expand=True,
                    children=[
                        Label("Available Wifi Networks"),
                        self.access_points_view
                    ]
                )
            ],
        )

        self.children = self.content_box

        bulk_connect(
            self.network_service,
            {
                "notify::active-connections": self.update_connection_elements,
                "notify::connections": self.update_connection_elements,
                "notify::access-points": self.update_access_point_elements,
            },
        )

    def update_connection_elements(self, *args):
        self.connections_box.children = []
        for con in self.get_connection_elements():
            self.connections_box.add(
                con
            )

    def update_access_point_elements(self, *args):
        self.access_points_box.children = self.get_access_point_elements()

    def toggle_connection_active(self, connection):
        self.network_service.toggle_connection_active(connection)

    def get_connection_elements(self):
        elements = []

        for con in self.network_service.connections:
            toggle_active_button = Button(
                style_classes="toggle-connection-active-button",
                child=Label(
                    style_classes="connection-element-icon",
                    markup=icons.active_connection
                    if self.network_service.is_connection_active(con)
                    else icons.inactive_connection,
                ),
                on_clicked=lambda *_, con=con: self.toggle_connection_active(con),
            )
            add_hover_cursor(toggle_active_button)

            elements.append(
                Box(
                    orientation="h",
                    spacing=10,
                    style_classes="connection-element",
                    h_expand=True,
                    children=[
                        toggle_active_button,
                        Label(
                            style_classes="connection-element-icon",
                            markup=get_connection_icon(con),
                        ),
                        Label(
                            style_classes="connection-element-label",
                            label=get_connection_id(con),
                        ),
                    ],
                )
            )

        return elements

    def get_access_point_elements(self):
        elements = []

        access_points = [
            ap for ap in self.network_service.access_points if ap.get_ssid() is not None
        ]
        access_points.sort(key=lambda ap: ap.get_strength(), reverse=True)

        for access_point in access_points:
            if access_point.get_ssid() is not None:
                ap_info = AccessPointInfo(access_point)

                elements.append(
                    Box(
                        style_classes="access-point-element",
                        orientation="h",
                        spacing=10,
                        children=[
                            Label(
                                style_classes="access-point-element-label",
                                label=ap_info.name,
                            ),
                            Label(
                                style_classes="access-point-element-icon",
                                markup=ap_info.strength_icon
                            )
                        ]
                    )
                )

        return elements
    

class AccessPointInfo():
    def __init__(self, access_point: NM.AccessPoint):
        self.path = access_point.get_path()
        self.name = truncate(
            NM.utils_ssid_to_utf8(access_point.get_ssid().get_data()),
            18
        )
        self.wpa_flags = access_point.get_wpa_flags()
        self.strength_icon = get_strength_icon(access_point.get_strength())