from fabric.core import Service
import gi
from util.singleton import Singleton
from gi.repository import Gkbd

gi.require_version("Gkbd", "3.0")


class KeyboardService(Service, Singleton):
    """This currently throws a segmentation fault and I'm not sure why.
    Will put this on hold for a while."""

    def __init__(self, **kwargs):
        raise NotImplementedError()
        super().__init__(**kwargs)

        self.kbd_config = Gkbd.Configuration.get()

        print(self.kbd_config)
