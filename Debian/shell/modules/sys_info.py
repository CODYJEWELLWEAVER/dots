from fabric.widgets.label import Label
from fabric import Fabricator

import config.icons as icons
from widgets.animated_circular_progress_bar import AnimatedCircularProgressBar

import psutil


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
            interval=1000,
            poll_from=poll_func,
            on_changed=self.on_value_changed
        )


    def on_value_changed(self, _, value):
        self.animate_value(value / 100.0)