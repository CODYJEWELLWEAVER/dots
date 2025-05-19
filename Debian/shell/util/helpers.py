import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def get_file_path_from_mpris_url(mpris_url: str) -> str:
    return mpris_url.replace("file://", "")


def get_icon_pixbuff(name):
    icon_theme = Gtk.IconTheme.get_default()
    return icon_theme.load_icon(name, 10, Gtk.IconLookupFlags.FORCE_SIZE)