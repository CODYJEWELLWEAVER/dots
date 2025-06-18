from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.entry import Entry

from fabric.utils.helpers import truncate, bulk_connect

from services.network import NetworkService
import config.icons as icons
from util.ui import add_hover_cursor

import gi
from gi.repository import NM

gi.require_version("NM", "1.0")


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


class NetworkOverview(Box):
    def __init__(self, do_show_connection_settings, **kwargs):
        super().__init__(
            name="network-overview",
            orientation="v",
            h_align="center",
            h_expand=True,
            **kwargs,
        )

        self.WIFI_ENABLED_LABEL = "On"
        self.WIFI_DISABLED_LABEL = "Off"

        self.do_show_connection_settings = do_show_connection_settings

        self.network_service = NetworkService.get_instance()
        self._active_wifi_connection = self.network_service.wifi_connection

        # Toggle Wireless Control
        self.toggle_wifi_icon = Label(
            style_classes="network-control-icon", markup=icons.wifi
        )
        self.toggle_wifi_label = Label(
            style_classes="network-control-label",
            label=self.WIFI_ENABLED_LABEL
            if self.network_service.wifi_enabled
            else self.WIFI_DISABLED_LABEL,
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
            "label",
            self.WIFI_ENABLED_LABEL if wifi_enabled else self.WIFI_DISABLED_LABEL,
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


class ConnectionSettings(Box):
    def __init__(self, on_close, **kwargs):
        super().__init__(
            name="connection-settings",
            style_classes="view-box",
            visible=True,
            orientation="v",
            v_expand=True,
            h_align="center",
            **kwargs,
        )

        self.network_service = NetworkService.get_instance()

        self.connections_list = Box(
            orientation="v",
            spacing=10,
            v_expand=True,
            children=self.get_connection_elements(),
        )
        self.connections_view = ScrolledWindow(
            style_classes="connection-settings-scrolled-window",
            v_expand=True,
            child=self.connections_list,
        )

        self.access_points_list = Box(
            orientation="v",
            spacing=10,
            v_expand=True,
            children=self.get_access_point_elements(),
        )
        self.access_points_view = ScrolledWindow(
            style_classes="connection-settings-scrolled-window",
            v_expand=True,
            child=self.access_points_list,
        )

        self.request_scan_button = Button(
            child=Label(style_classes="connection-settings-icon", markup=icons.refresh),
            on_clicked=lambda *_: self.network_service.request_scan(),
        )
        add_hover_cursor(self.request_scan_button)

        self.overview_box = Box(
            name="connection-settings-overview",
            orientation="h",
            spacing=40,
            v_expand=True,
            v_align="center",
            children=[
                Box(
                    orientation="v",
                    spacing=10,
                    children=[Label("Saved Connections"), self.connections_view],
                ),
                Box(
                    orientation="v",
                    spacing=10,
                    children=[
                        Box(
                            spacing=20,
                            orientation="h",
                            h_align="center",
                            children=[
                                self.request_scan_button,
                                Label("Available Wifi Networks"),
                            ],
                        ),
                        self.access_points_view,
                    ],
                ),
                Box(
                    children=Button(
                        name="close-connection-settings-button",
                        child=Label(
                            style_classes="connection-settings-icon",
                            markup=icons.arrow_right,
                        ),
                        on_clicked=on_close,
                    )
                ),
            ],
        )

        self.password_entry_label = Label(
            name="password-entry-label", label="Enter password:"
        )
        self.password_entry = Entry(
            name="password-entry",
            password=True,
        )
        self.connect_button = Button(
            style_classes="password-entry-button",
            label="Connect",
        )
        self.cancel_button = Button(
            style_classes="password-entry-button",
            label="Cancel",
            on_clicked=lambda *_: self.password_entry_box.set_visible(False),
        )
        add_hover_cursor(self.cancel_button)

        self.password_entry_box = Box(
            name="password-entry-box",
            spacing=20,
            orientation="h",
            h_expand=True,
            h_align="center",
            visible=False,
            children=[
                self.cancel_button,
                self.password_entry_label,
                self.password_entry,
                self.connect_button,
            ],
        )

        self.children = [self.password_entry_box, self.overview_box]

        bulk_connect(
            self.network_service,
            {
                "notify::active-connections": self.update_connection_elements,
                "notify::connections": self.update_connection_elements,
                "notify::access-points": self.update_access_point_elements,
            },
        )

    def update_connection_elements(self, *args):
        self.connections_list.children = self.get_connection_elements()

    def update_access_point_elements(self, *args):
        self.access_points_list.children = self.get_access_point_elements()

    def show_password_entry_box(self, ap_info):
        def get_password_and_connect(button):
            entered_password = self.password_entry.get_text()
            if entered_password != "":
                self.network_service.connect_to_access_point(ap_info, entered_password)
                self.password_entry_box.set_visible(False)
                self.password_entry.set_property("text", "")

        # TODO: surely there is a better way to do this?
        # remakes connect button to link it to correct action
        self.password_entry_box.remove(self.connect_button)
        self.connect_button = Button(
            style_classes="password-entry-button",
            label="Connect",
            on_clicked=get_password_and_connect,
        )
        add_hover_cursor(self.connect_button)
        self.password_entry_box.add(self.connect_button)

        self.password_entry_box.set_visible(True)

    def get_connection_elements(self):
        elements = []

        for connection in self.network_service.connections:
            connection_element = ConnectionElement(
                is_active=self.network_service.is_connection_active(connection),
                connection_icon=get_connection_icon(connection),
                connection_id=get_connection_id(connection),
                toggle_active_callback=lambda *_, con=connection: (
                    self.network_service.toggle_connection_active(con)
                ),
                delete_callback=lambda *_, con=connection: (
                    self.network_service.delete_connection(con)
                ),
            )

            elements.append(connection_element)

        return elements

    def get_access_point_elements(self):
        elements = []

        access_points = self.network_service.access_points
        access_points.sort(key=lambda ap: ap.get_strength(), reverse=True)

        for access_point in access_points:
            if access_point.get_ssid() is not None:
                ap_info = AccessPointInfo(access_point)

                def on_connect(*args, ap_info=ap_info):
                    if ap_info.is_secured:
                        self.show_password_entry_box(ap_info)
                    else:
                        self.network_service.connect_to_access_point(ap_info, None)

                access_point_element = AccessPointElement(
                    ap_info=ap_info, connect_callback=on_connect
                )

                elements.append(access_point_element)

        return elements


class ConnectionElement(Box):
    def __init__(
        self,
        is_active: bool,
        connection_icon: str,
        connection_id: str,
        toggle_active_callback,
        delete_callback,
        **kwargs,
    ):
        toggle_active_button = Button(
            style_classes="toggle-connection-active-button",
            child=Label(
                style_classes="connection-element-icon",
                markup=icons.active_connection
                if is_active
                else icons.inactive_connection,
            ),
            on_clicked=toggle_active_callback,
        )
        add_hover_cursor(toggle_active_button)

        delete_button = Button(
            style_classes="delete-connection-button",
            child=Label(style_classes="connection-settings-icon", markup=icons.delete),
            on_clicked=delete_callback,
        )
        add_hover_cursor(delete_button)

        super().__init__(
            orientation="h",
            spacing=10,
            style_classes="connection-settings-element",
            children=[
                delete_button,
                Label(
                    style_classes="connection-settings-icon",
                    markup=connection_icon,
                ),
                toggle_active_button,
                Label(
                    style_classes="connection-element-label",
                    label=connection_id,
                ),
            ],
            **kwargs,
        )


class AccessPointInfo:
    def __init__(self, access_point: NM.AccessPoint):
        full_name = NM.utils_ssid_to_utf8(access_point.get_ssid().get_data())

        self.ssid = access_point.get_ssid()
        self.path = access_point.get_path()
        self.display_name = truncate(full_name, 18)
        self.full_name = full_name
        self.strength_icon = get_strength_icon(access_point.get_strength())
        self.is_secured = (
            access_point.get_rsn_flags() != 0  # Check if WPA v2 secured
            or access_point.get_wpa_flags() != 0  # Check if WPA v1 secured
        )


class AccessPointElement(Box):
    def __init__(
        self,
        ap_info: AccessPointInfo,
        connect_callback,
        **kwargs,
    ):
        connect_button = Button(
            child=Label(
                style_classes="connection-settings-icon",
                markup=icons.link_add,
            ),
            on_clicked=connect_callback,
        )
        add_hover_cursor(connect_button)

        super().__init__(
            style_classes="connection-settings-element",
            orientation="h",
            spacing=10,
            children=[
                Label(
                    style_classes="connection-settings-icon",
                    markup=icons.locked if ap_info.is_secured else icons.unlocked,
                ),
                connect_button,
                Label(
                    style_classes="access-point-element-label",
                    label=ap_info.display_name,
                ),
                Label(
                    style_classes="connection-settings-icon",
                    markup=ap_info.strength_icon,
                ),
            ],
            **kwargs,
        )
