from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.stack import Stack
from fabric.widgets.box import Box
from fabric.widgets.label import Label

from services.volume import VolumeService
import config.icons as Icons
from config.osd import TIMEOUT_DELAY

from gi.repository import GLib


def get_volume_icon(volume: float, is_muted: bool) -> str:
    if is_muted:
        return Icons.volume_muted

    if volume >= 0.5:
        return Icons.volume_high
    elif volume > 0.0:
        return Icons.volume_low
    else:
        return Icons.volume_off


def get_volume_percent_label(volume: float, is_muted: bool) -> str:
    if is_muted:
        return "MUTED"

    percent = int(volume * 100)
    return f"{percent}%"


class OSD(Window):
    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="center",
            exclusivity="none",
            h_align="center",
            v_align="center",
            visible=False,
            **kwargs,
        )

        self.timeout_id = None

        self.volume_service = VolumeService.get_instance()

        self.volume_icon = Label(
            name="osd-volume-icon",
            markup=get_volume_icon(
                self.volume_service.volume, self.volume_service.is_muted
            ),
        )
        self.volume_percent = Label(
            name="osd-volume-percent",
            label=get_volume_percent_label(
                self.volume_service.volume, self.volume_service.is_muted
            ),
        )
        self.volume_element = Box(
            spacing=20,
            orientation="v",
            children=[self.volume_icon, self.volume_percent],
        )

        # using a stack so I can easily toggle between
        # different elements once I get Gkbd working
        self.content_stack = Stack(
            name="osd-content-stack",
            transition_type="crossfade",
            transition_duration=300,
            children=[self.volume_element],
        )

        self.add(self.content_stack)

        self.volume_service.connect("changed", self.on_volume_changed)

        self.hide()

    def show_volume_element(self):
        self.show()
        self.content_stack.set_visible_child(self.volume_element)

    def on_timeout_expired(self, *args):
        self.hide()
        return False

    def on_volume_changed(self, *args):
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None

        volume = self.volume_service.volume
        is_muted = self.volume_service.is_muted

        self.volume_icon = Label(
            name="osd-volume-icon", markup=get_volume_icon(volume, is_muted)
        )

        self.volume_percent.set_property(
            "label", get_volume_percent_label(volume, is_muted)
        )

        self.volume_element.children = [self.volume_icon, self.volume_percent]

        self.show_volume_element()

        self.timeout_id = GLib.timeout_add(TIMEOUT_DELAY, self.on_timeout_expired)
