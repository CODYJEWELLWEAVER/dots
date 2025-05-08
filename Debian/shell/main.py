import setproctitle
from fabric import Application
from fabric.utils import get_relative_path
from modules.bar import Bar


if __name__ == "__main__":
    APP_NAME = "Fabric-Shell"

    setproctitle.setproctitle(APP_NAME)

    bar = Bar(name="main-bar")

    app = Application(APP_NAME, bar)

    app.set_stylesheet_from_file(
        get_relative_path("main.css")
    )

    app.run()