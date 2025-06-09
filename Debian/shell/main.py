import setproctitle
from fabric import Application
from fabric.utils import get_relative_path, monitor_file
from modules.bar import Bar
from modules.control_panel import ControlPanel

import asyncio
from gi.events import GLibEventLoopPolicy


def main():
    APP_NAME = "Fabric-Shell"

    asyncio.set_event_loop_policy(GLibEventLoopPolicy())

    setproctitle.setproctitle(APP_NAME)

    control_panel = ControlPanel()
    bar = Bar(control_panel)

    app = Application(APP_NAME, bar, control_panel, open_inspector=True)

    def apply_stylesheet(*_):
        return app.set_stylesheet_from_file(get_relative_path("main.css"))

    style_monitor = monitor_file(get_relative_path("./styles"))
    style_monitor.connect("changed", apply_stylesheet)

    app.set_stylesheet_from_file(get_relative_path("main.css"))

    app.run()


if __name__ == "__main__":
    main()
