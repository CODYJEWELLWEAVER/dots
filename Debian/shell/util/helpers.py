import gi
from gi.repository import Gtk
import os
import platform
import locale

gi.require_version("Gtk", "3.0")


def get_file_path_from_mpris_url(mpris_url: str) -> str:
    return mpris_url.replace("file://", "")


def get_icon_pixbuff(name):
    icon_theme = Gtk.IconTheme.get_default()
    return icon_theme.load_icon(name, 10, Gtk.IconLookupFlags.FORCE_SIZE)


def get_user_login_name():
    login_name = os.getenv("LOGNAME")
    return login_name if login_name else "user"


def get_system_node_name():
    node_name = platform.node()
    return node_name if node_name != "" else "system"


def get_country_code():
    language_code = locale.getlocale()[0]

    if language_code is None:
        return "US"

    try:
        return language_code.split("_")[1]
    except IndexError:
        return "US"
