from typing import Iterable
from fabric.core.service import Service, Property

from util.singleton import Singleton

import gi
from gi.repository import NM

gi.require_version("NM", "1.0")


class NetworkService(Service, Singleton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._client = NM.Client.new(None)
        print(self.active_connections)
        self._devices = self._client.get_devices()
        print(self._devices)
        ap_ssid = self._devices[2].get_active_access_point().get_ssid()
        print(NM.utils_ssid_to_utf8(ap_ssid.get_data()))
        print(self.access_points)

    @Property(Iterable[NM.ActiveConnection], flags="readable")
    def active_connections(self) -> Iterable[NM.ActiveConnection]:
        return self._client.get_active_connections()

    @Property(Iterable[NM.AccessPoint], flags="readable")
    def access_points(self) -> Iterable[NM.AccessPoint]:
        self._devices[2].request_scan_async(None)
        wifi_devices = [
            dev for dev in self._devices if dev.get_device_type() == NM.DeviceType.WIFI
        ]

        _access_points = []

        for device in wifi_devices:
            for ap in device.get_access_points():
                _access_points.append(ap)

        return _access_points
