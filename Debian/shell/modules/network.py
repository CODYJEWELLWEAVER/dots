from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.utils.helpers import truncate, bulk_connect

from services.network import NetworkService
import config.icons as icons

import gi
from gi.repository import NM

gi.require_version("NM", "1.0")


WIFI_ENABLED_LABEL = "On"
WIFI_DISABLED_LABEL = "Off"


class NetworkControl(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="network-control",
            orientation="v",
            h_align="center",
            h_expand=True,
            **kwargs,
        )

        self.network_service = NetworkService.get_instance()
        self._active_wifi_connection = self.network_service.wifi_connection

        # Control for wifi networks
        self.wifi_icon = Label(style_classes="network-control-icon", markup=icons.wifi)
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
                self.wifi_icon,
                self.wifi_connection_label,
                self.wifi_status_icon,
            ],
        )
        self.wifi = Button(
            style_classes="network-control-button",
            h_expand=True,
            h_align="center",
            child=self.wifi_child_box,
        )

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

        self.children = [
            Box(
                spacing=10,
                orientation="h",
                h_expand=True,
                h_align="fill",
                children=[self.wifi, self.toggle_wifi],
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
            self.wifi_icon,
            self.wifi_connection_label,
            self.wifi_status_icon,
        ]


def get_connection_id(connection: NM.ActiveConnection) -> str:
    if connection is not None:
        return truncate(connection.get_id(), 24)
    else:
        return "Disconnected"
