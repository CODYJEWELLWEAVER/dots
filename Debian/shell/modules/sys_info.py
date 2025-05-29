from fabric.widgets.label import Label
from fabric.widgets.box import Box
from fabric import Fabricator

import config.icons as icons
import config.network as network
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
            **kwargs
        )


        self.children = Label(
            markup=icon,
            style_classes="sys-info-icon"
        )


        self.value_fabricator = Fabricator(
            interval=500,
            poll_from=poll_func,
            on_changed=self.on_value_changed
        )


    def on_value_changed(self, _, value):
        self.animate_value(value / 100.0)



class CPUUsage(Box):
    def __init__(self, **kwargs):
        super().__init__(
            style_classes="sys-info-box",
            children=SysInfoCircularBar(
                style_classes="sys-info-circular-bar",
                icon=icons.cpu,
                poll_func=lambda *_: psutil.cpu_percent()
            ),
            **kwargs
        )


class GPUUsage(Box):
    def __init__(self, **kwargs):
        super().__init__(
            style_classes="sys-info-box",
            children=SysInfoCircularBar(
                style_classes="sys-info-circular-bar",
                icon=icons.gpu,
                poll_func=self._get_usage
            )
        )


    def _get_usage(self, *_):
        return nvsmi.DeviceQuery("utilization.gpu")['gpu'][0]\
            ['utilization']['gpu_util']


class RAM(Box):
    def __init__(self, **kwargs):
        super().__init__(
            style_classes="sys-info-box",
            children=SysInfoCircularBar(
                style_classes="sys-info-circular-bar",
                icon=icons.ram,
                poll_func=lambda *_: psutil.virtual_memory().percent
            ),
            **kwargs
        )


class Disk(Box):
    def __init__(self, **kwargs):
        super().__init__(
            style_classes="sys-info-box",
            children=SysInfoCircularBar(
                style_classes="sys-info-circular-bar",
                icon=icons.disk,
                poll_func=lambda *_: psutil.disk_usage("/").percent
            ),
            **kwargs
        )


class Network(Box):
    def __init__(self, **kwargs):
        super().__init__(
            style_classes="sys-info-box",
            children=Label(
                style_classes="sys-info-icon",
                markup=icons.wifi
            ),
            v_align="center",
            h_align="center",
            h_expand=True,
            v_expand=True,
            **kwargs
        )


        self.connection_monitor = Fabricator(
            interval=500,
            poll_from=self._get_connection_info,
            on_changed=self._on_connection_changed
        )

    
    def _get_connection_info(self, *_) -> str | None:
        connections = psutil.net_if_stats()

        # see config.network for configuration
        if network.ethernet in connections:
            return network.ethernet
        elif network.wifi in connections:
            return network.wifi
        else:
            return None
        

    def _on_connection_changed(self, f, connection_name):
        if connection_name == network.ethernet:
            icon = icons.ethernet
        elif connection_name == network.wifi:
            icon = icons.wifi
        else:
            icon = icons.no_network

        self.children = Label(
            style_classes="sys-info-icon",
            markup=icon
        )