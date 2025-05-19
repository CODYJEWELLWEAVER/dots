import setproctitle
from fabric import Application
from fabric.utils import get_relative_path, monitor_file
from modules.bar import StatusBar
from modules.media import Media
from modules.power import PowerControl

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Playerctl


if __name__ == "__main__":
    APP_NAME = "Fabric-Shell"

    setproctitle.setproctitle(APP_NAME)

    player_manager = Playerctl.PlayerManager()

    media = Media(player_manager)
    bar = StatusBar()
    power = PowerControl()

    app = Application(APP_NAME, media, bar, power, open_inspector=False)

    def apply_stylesheet(*_):
        return app.set_stylesheet_from_file(
        get_relative_path("main.css")
    )

    style_monitor = monitor_file(get_relative_path("./styles"))
    style_monitor.connect("changed", apply_stylesheet)

    app.set_stylesheet_from_file(
        get_relative_path("main.css")
    )

    app.run()
    