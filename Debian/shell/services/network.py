from fabric.core.service import Service, Property
from fabric.utils.helpers import bulk_connect, exec_shell_command_async

from util.singleton import Singleton
from loguru import logger

import gi
from gi.repository import NM, GLib

from typing import List, Literal

gi.require_version("NM", "1.0")


class NetworkService(Service, Singleton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._client = NM.Client.new(None)
        self._devices = self._client.get_devices()

        # TODO: Set this up so that only one wifi device is used at a time
        for wifi_device in self.get_wifi_devices():
            self.connect_wifi_device_to_notify_access_points(wifi_device)

        bulk_connect(
            self._client,
            {
                "device-added": self.on_device_added,
                "active-connection-added": self.on_active_connection,
                "active-connection-removed": self.on_active_connection,
            },
        )

        """ self._client.add_and_activate_connection2(
            NM.RemoteConnection(),
            self.get_wifi_devices()[0],
            self.access_points[0].get_path(),
            GLib.Variant("a{sv}", None),
            None,
            None,
            None
        ) """

    @Property(Literal["wireless", "ethernet", "disconnected"], flags="readable")
    def connection_type(
        self,
    ) -> Literal["wireless", "ethernet", "disconnected"]:
        """primary_connection = self._client.get_primary_connection()

        if primary_connection is not None:
            connection_type = primary_connection.get_connection_type()
            if "wireless" in connection_type:
                return "wireless"
            elif "ethernet" in connection_type:
                return "ethernet" """

        # if the primary connection is not defined, we could still have a connection
        # TODO: Check why the primary connection will not update? I probably have a
        # misunderstanding.

        active_cons = self.active_connections
        if len(active_cons) > 0:
            # this is somewhat hacky, need to find a nicer solution
            connection_type = active_cons[0].get_connection_type()
            if "wireless" in connection_type:
                return "wireless"
            elif "ethernet" in connection_type:
                return "ethernet"

        return "disconnected"

    @Property(List[NM.ActiveConnection], flags="readable")
    def active_connections(self) -> List[NM.ActiveConnection]:
        active_connections = self._client.get_active_connections()
        return [con for con in active_connections if con.get_id() != "lo"]

    @Property(NM.ActiveConnection, flags="readable")
    def wifi_connection(self) -> NM.ActiveConnection | None:
        for con in self.active_connections:
            if "wireless" in con.get_connection_type():
                return con

        return None

    @Property(bool, default_value=True, flags="readable")
    def wifi_enabled(self) -> bool:
        return self._client.wireless_get_enabled()

    @Property(List[NM.AccessPoint], flags="readable")
    def access_points(self) -> List[NM.AccessPoint]:
        _access_points = []

        for device in self.get_wifi_devices():
            for ap in device.get_access_points():
                _access_points.append(ap)

        return _access_points

    def get_wifi_devices(self) -> List[NM.DeviceWifi]:
        return [
            dev for dev in self._devices if dev.get_device_type() == NM.DeviceType.WIFI
        ]

    def connect_wifi_device_to_notify_access_points(self, device):
        # link wifi devices to notify when they
        # add or remove access points
        if device in self.get_wifi_devices():
            notify_access_points = lambda *_: self.notify("access-points")
            bulk_connect(
                device,
                {
                    "access-point-added": notify_access_points,
                    "access-point-removed": notify_access_points,
                },
            )

    @logger.catch
    def toggle_wireless(self):
        enabled = self.wifi_enabled
        self._client.dbus_set_property(
            NM.DBUS_PATH,
            NM.DBUS_INTERFACE,
            "WirelessEnabled",
            GLib.Variant("b", not enabled),
            -1,  # use default timeout
            None,
            lambda *_: self.notify("wifi-enabled"),
            None,
        )

    # TODO: Change this to use NM module
    def enable_connection_by_id(self, id: str):
        exec_shell_command_async(
            f"nmcli con up {id}", self.log_connection_enable_up_down
        )

    def disable_connection_by_id(self, id: str):
        exec_shell_command_async(
            f"nmcli con down {id}", self.log_connection_enable_up_down
        )

    def log_connection_enable_up_down(self, msg: str):
        logger.info(msg)

    def request_scan(self):
        if self._client.wireless_get_enabled():
            for dev in self.get_wifi_devices():
                dev.request_scan_async(None, self.finish_scan_callback)

    def finish_scan_callback(self, device, result):
        logger.debug(f"Scan callback result: {device.request_scan_finish(result)}")

    def on_device_added(self, client, device):
        if device.get_device_type() == NM.DeviceType.WIFI:
            self.connect_wifi_device_to_notify_access_points(device)

    def on_active_connection(self, client, connection):
        self.notify("active-connections")
        self.notify("connection-type")
        self.notify("wifi-connection")
