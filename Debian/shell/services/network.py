from fabric.core.service import Service, Property
from fabric.utils.helpers import bulk_connect, exec_shell_command_async

from config.network import DEFAULT_WIFI_IFACE
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
        self._wifi_device = self.get_default_wifi_device()
        
        # TODO: Double check this is set correctly if no wifi device is found
        self._wifi_enabled = self._client.wireless_get_enabled()

        self.connect_wifi_device_to_notify_access_points(self._wifi_device)

        bulk_connect(
            self._client,
            {
                "device-added": self.on_device_added,
                "active-connection-added": self.on_active_connection,
                "active-connection-removed": self.on_active_connection,
                "connection-added": self.on_connection,
                "connection-removed": self.on_connection,
            },
        )

        # scan for access-points initially
        self.request_scan()

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

        active_connections = self.active_connections
        if len(active_connections) > 0:
            # this is somewhat hacky, need to find a nicer solution
            connection_type = active_connections[0].get_connection_type()
            if "wireless" in connection_type:
                return "wireless"
            elif "ethernet" in connection_type:
                return "ethernet"

        return "disconnected"

    @Property(List[NM.RemoteConnection], flags="readable")
    def connections(self) -> List[NM.RemoteConnection]:
        return [con for con in self._client.get_connections() if con.get_id() != "lo"]

    @Property(List[NM.ActiveConnection], flags="readable")
    def active_connections(self) -> List[NM.ActiveConnection] | None:
        active_connections = self._client.get_active_connections()
        if active_connections is not None:
            # ignore loopback connection
            return [con for con in active_connections if con.get_id() != "lo"]
        return None

    @Property(NM.ActiveConnection, flags="readable")
    def wifi_connection(self) -> NM.ActiveConnection | None:
        for con in self.active_connections:
            if "wireless" in con.get_connection_type():
                return con

        return None

    @Property(bool, default_value=True, flags="readable")
    def wifi_enabled(self) -> bool:
        return self._wifi_enabled

    @wifi_enabled.setter
    def wifi_enabled(self, enabled) -> None:
        self._wifi_enabled = enabled

    @Property(List[NM.AccessPoint], flags="readable")
    def access_points(self) -> List[NM.AccessPoint]:
        return self._wifi_device.get_access_points()
    
    def get_default_wifi_device(self) -> NM.DeviceWifi | None:
        wifi_devices = self.get_wifi_devices()
        if len(wifi_devices) > 0:
            for dev in wifi_devices:
                if dev.get_iface() == DEFAULT_WIFI_IFACE:
                    return dev
            return wifi_devices[0]
        else:
            return None

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

    def toggle_wireless(self):
        enabled = self.wifi_enabled
        self._client.dbus_set_property(
            NM.DBUS_PATH,
            NM.DBUS_INTERFACE,
            "WirelessEnabled",
            GLib.Variant("b", not enabled),
            -1,  # use default timeout
            None,
            None,
            None,
        )
        self._wifi_enabled = not enabled
        self.notify("wifi-enabled")

    def toggle_connection_active(self, connection: NM.RemoteConnection):
        if not self.is_connection_active(connection):
            self._client.activate_connection_async(
                    connection,
                    None,  # use default device
                    connection.get_path(),
                    None,
                    self.activate_finish_callback,
                    None,
                )
        else:
            active_connection = self.get_active_connection_from_remote(connection)
            if active_connection is not None:
                self._client.deactivate_connection_async(
                    active_connection,
                    None,
                    self.deactivate_finish_callback,
                    None
                )
    
    @logger.catch
    def activate_finish_callback(self, device, result, data):
        self._client.activate_connection_finish(result)

    @logger.catch
    def deactivate_finish_callback(self, device, result, data):
        self._client.deactivate_connection_finish(result)

    def request_scan(self):
        if self._client.wireless_get_enabled():
            self._wifi_device.request_scan_async(None, self.finish_scan_callback)

    @logger.catch
    def finish_scan_callback(self, device, result):
        device.request_scan_finish(result)

    def on_device_added(self, client, device):
        if device.get_device_type() == NM.DeviceType.WIFI:
            self._wifi_device = self.get_default_wifi_device()

    def on_active_connection(self, client, connection):
        self.notify("active-connections")
        self.notify("connection-type")
        self.notify("wifi-connection")

    def on_connection(self, client, connection):
        self.notify("connections")

    def is_connection_active(self, connection) -> bool:
        active_con_uuids = [con.get_uuid() for con in self.active_connections]
        return connection.get_uuid() in active_con_uuids
    
    def get_active_connection_from_remote(self, remote) -> NM.ActiveConnection | None:
        for con in self.active_connections:
            if con.get_uuid() == remote.get_uuid():
                return con
            
        return None