from fabric.widgets.label import Label
from fabric.widgets.box import Box
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric import Fabricator

from services.network import NetworkService
import config.icons as Icons
from widgets.animated_circular_progress_bar import AnimatedCircularProgressBar

import psutil
from pynvml_utils import nvidia_smi

nvsmi = nvidia_smi.getInstance()


# TODO: Move fabricators into services so they can be shared efficiently


class SysInfoCircularBar(AnimatedCircularProgressBar):
    def __init__(self, icon, poll_func, **kwargs):
        super().__init__(
            h_align="center",
            v_align="center",
            size=50,
            line_width=6,
            value=0,
            start_angle=90,
            end_angle=450,
            **kwargs,
        )

        self.children = Label(markup=icon, style_classes="sys-info-icon")

        self.value_fabricator = Fabricator(
            interval=500, poll_from=poll_func, on_changed=self.on_value_changed
        )

    def on_value_changed(self, _, value):
        self.animate_value(value / 100.0)


class CPUUsage(Box):
    def __init__(self, **kwargs):
        super().__init__(
            h_align="center",
            v_align="center",
            style_classes="sys-info-box",
            children=SysInfoCircularBar(
                style_classes="sys-info-circular-bar",
                icon=Icons.cpu,
                poll_func=lambda *_: psutil.cpu_percent(),
            ),
            **kwargs,
        )


class GPUUsage(Box):
    def __init__(self, **kwargs):
        super().__init__(
            h_align="center",
            v_align="center",
            style_classes="sys-info-box",
            children=SysInfoCircularBar(
                style_classes="sys-info-circular-bar",
                icon=Icons.gpu,
                poll_func=self._get_usage,
            ),
            **kwargs
        )

    def _get_usage(self, *_):
        return nvsmi.DeviceQuery("utilization.gpu")["gpu"][0]["utilization"]["gpu_util"]


class RAM(Box):
    def __init__(self, **kwargs):
        super().__init__(
            h_align="center",
            v_align="center",
            style_classes="sys-info-box",
            children=SysInfoCircularBar(
                style_classes="sys-info-circular-bar",
                icon=Icons.ram,
                poll_func=lambda *_: psutil.virtual_memory().percent,
            ),
            **kwargs,
        )


class Disk(Box):
    def __init__(self, **kwargs):
        super().__init__(
            h_align="center",
            v_align="center",
            style_classes="sys-info-box",
            children=SysInfoCircularBar(
                style_classes="sys-info-circular-bar",
                icon=Icons.disk,
                poll_func=lambda *_: psutil.disk_usage("/").percent,
            ),
            **kwargs,
        )


class NetworkInfo(Box):
    def __init__(self, **kwargs):
        super().__init__(
            style_classes="sys-info-box",
            v_align="center",
            h_align="center",
            h_expand=True,
            v_expand=True,
            **kwargs,
        )

        self.network_service = NetworkService.get_instance()

        self.network_status_icon_box = Box()

        self.network_status_bar = CircularProgressBar(
            name="network-status-circular-bar",
            style_classes="connected",
            h_align="center",
            v_align="center",
            size=50,
            line_width=6,
            child=self.network_status_icon_box,
        )

        self.children = self.network_status_bar

        self.network_service.connect(
            "notify::primary-connection-type", self.on_notify_connection_type
        )
        # run once to make sure the status label is initialized
        self.on_notify_connection_type()

    def on_notify_connection_type(self, *args) -> None:
        print(self.network_service.primary_connection_type)
        connection_type = self.network_service.primary_connection_type
        if connection_type == "wireless":
            icon = Icons.wifi
        elif connection_type == "ethernet":
            icon = Icons.ethernet
        else:
            icon = Icons.no_network

        self.network_status_icon_box.children = Label(
            style_classes="sys-info-icon", markup=icon
        )

        if connection_type == "disconnected":
            self.network_status_bar.remove_style_class("connected")
            self.network_status_bar.add_style_class("not-connected")
        else:
            self.network_status_bar.remove_style_class("not-connected")
            self.network_status_bar.add_style_class("connected")
