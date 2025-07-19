from fabric.core.service import Service, Property
from fabric.utils.helpers import bulk_connect

from config.network import DEFAULT_WIFI_IFACE
from util.singleton import Singleton
from loguru import logger
import dbus

import gi
from gi.repository import NM, GLib

from typing import List, Literal

gi.require_version("NM", "1.0")

DBUS = dbus.SystemBus()


class NetworkService(Service, Singleton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._client = NM.Client.new(None)
        self._devices = self._client.get_devices()
        self._wifi_device = self.get_default_wifi_device()

        self._wifi_enabled = (
            self._client.wireless_get_enabled()
            if self.get_wifi_devices() != []
            else False
        )

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

    @Property(Literal["wireless", "ethernet", "disconnected"], flags="readable")
    def primary_connection_type(
        self,
    ) -> Literal["wireless", "ethernet", "disconnected"]:
        primary_connection = self._client.get_primary_connection()

        if primary_connection is not None:
            connection_type = primary_connection.get_connection_type()
            if "wireless" in connection_type:
                return "wireless"
            elif "ethernet" in connection_type:
                return "ethernet"
        else:
            active_connections = self.active_connections
            if len(active_connections) > 0:
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
        return (
            self._wifi_device.get_access_points()
            if self._wifi_device is not None
            else []
        )

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

    def connect_wifi_device_to_notify_access_points(self, device) -> None:
        # link wifi devices to notify when they
        # add or remove access points
        if device is not None:

            def notify_access_points(*args):
                self.notify("access-points")

            bulk_connect(
                device,
                {
                    "access-point-added": notify_access_points,
                    "access-point-removed": notify_access_points,
                },
            )

    def connect_to_access_point(self, ap_info, password: str | None) -> None:
        if self.is_access_point_connected(ap_info.ssid):
            return

        self.add_wifi_connection(
            full_name=ap_info.full_name,
            ssid=ap_info.ssid,
            path=ap_info.path,
            is_secured=ap_info.is_secured,
            password=password,
        )

    def add_wifi_connection(
        self,
        full_name: str,
        ssid: GLib.Bytes,
        path: str,
        is_secured: bool,
        password: str | None,
    ) -> None:
        # create new connection object and fill the settings
        connection = NM.RemoteConnection()
        connection.set_path(path)

        # general connection settings
        connection_settings = NM.SettingConnection()
        connection_settings.props.id = full_name
        connection_settings.props.type = "802-11-wireless"
        connection_settings.uuid = NM.utils_uuid_generate()
        connection.add_setting(connection_settings)

        # wifi setting
        wireless_settings = NM.SettingWireless()
        wireless_settings.props.ssid = ssid
        connection.add_setting(wireless_settings)

        # wifi security settings
        if is_secured:
            wireless_security_settings = NM.SettingWirelessSecurity()
            wireless_security_settings.props.auth_alg = "open"
            wireless_security_settings.props.key_mgmt = "wpa-psk"
            wireless_security_settings.props.psk = password
            connection.add_setting(wireless_security_settings)

        self._client.add_and_activate_connection_async(
            connection,
            self.get_default_wifi_device(),  # device
            path,  # specific object
            None,  # cancellable
            self.add_connection_and_activate_finish_callback,
            None,  # user data
        )

    @logger.catch
    def add_connection_and_activate_finish_callback(self, client, result, data) -> None:
        self._client.add_and_activate_connection_finish(result)

    def delete_connection(self, connection: NM.RemoteConnection):
        connection.delete_async(
            None,
            self.delete_connection_finish_callback,
            None,
        )

    @logger.catch
    def delete_connection_finish_callback(self, connection, result, data):
        connection.delete_finish(result)

    def toggle_wireless(self):
        if self.get_wifi_devices() != []:
            enabled = self.wifi_enabled
            self._client.dbus_set_property(
                NM.DBUS_PATH,
                NM.DBUS_INTERFACE,
                "WirelessEnabled",  # property name
                GLib.Variant("b", not enabled),  # value
                -1,  # timeout (in msec), use default
                None,
                None,  # callback, is not a reliable way to adjust ui elements
                None,  # user data for callback
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
                    active_connection, None, self.deactivate_finish_callback, None
                )

    @logger.catch
    def activate_finish_callback(self, device, result, data):
        self._client.activate_connection_finish(result)

    @logger.catch
    def deactivate_finish_callback(self, device, result, data):
        self._client.deactivate_connection_finish(result)

    def request_scan(self):
        if self.wifi_enabled:
            self._wifi_device.request_scan_async(None, self.finish_scan_callback)

    @logger.catch
    def finish_scan_callback(self, device, result):
        device.request_scan_finish(result)

    def on_device_added(self, client, device):
        if device.get_device_type() == NM.DeviceType.WIFI:
            self._wifi_device = self.get_default_wifi_device()

    def on_active_connection(self, client, connection):
        self.notify("active-connections")
        self.notify("primary-connection-type")
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

    def is_access_point_connected(self, ssid):
        for connection in self.connections:
            general_settings = connection.get_setting_connection()
            if general_settings.props.type != "802-11-wireless":
                continue

            wireless_settings = connection.get_setting_wireless()
            if wireless_settings.props.ssid.get_data() == ssid.get_data():
                return True

        return False
