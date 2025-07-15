from fabric.core import Service, Property, Signal
from fabric.utils import invoke_repeater

from util.singleton import Singleton
import pulsectl


class VolumeService(Service, Singleton):
    """
    Service to allow seamless connection between media bar and osd
    volume displays.
    """

    @Signal("changed")
    def changed(self) -> None: ...

    @Property(float, flags="read-write")
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, new_volume):
        self._volume = new_volume
        self.changed()

    @Property(bool, default_value=False, flags="read-write")
    def is_muted(self) -> bool:
        return self._muted

    @is_muted.setter
    def is_muted(self, new_muted):
        self._muted = new_muted
        self.changed()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pulse = pulsectl.Pulse()

        self._volume = 0.0
        self._muted = False

        invoke_repeater(100, self.watch_volume)

    def watch_volume(self, *args):
        sink = self.pulse.sink_default_get()
        new_volume = sink.volume.value_flat
        new_is_muted = sink.mute
        if new_volume != self.volume:
            self.volume = new_volume
        if new_is_muted != self.is_muted:
            self.is_muted = new_is_muted

        return True
