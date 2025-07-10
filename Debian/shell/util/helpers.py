from gi.repository import Gtk, GdkPixbuf
import os
import platform
import locale
from pathlib import Path

from loguru import logger

from config.storage import STORAGE_DIRECTORY


def get_file_path_from_mpris_url(mpris_url: str) -> str:
    return Path.from_uri(mpris_url).__fspath__()


def get_app_icon_pixbuf(
    name: str, width: int, height: int, preserve_aspect_ratio: bool = True
) -> GdkPixbuf.Pixbuf:
    icon_theme = Gtk.IconTheme.get_default()
    icon_info = icon_theme.lookup_icon(name, width, 0)  # No Flags
    if icon_info is not None:
        icon_path = icon_info.get_filename()
        icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            icon_path, width, height, preserve_aspect_ratio
        )
        return icon_pixbuf

    return None


def get_user_login_name():
    login_name = os.getenv("LOGNAME")
    return login_name if login_name else "user"


def get_system_node_name():
    node_name = platform.node()
    return node_name if node_name != "" else "system"


def get_country_code():
    try:
        language_code = locale.getlocale()[0]
        return language_code.split("_")[1]
    except IndexError:
        logger.warning("Could not find current country code, defaulting to US.")
    finally:
        return "US"


def init_data_directory():
    storage_directory = Path(STORAGE_DIRECTORY)
    storage_directory.mkdir(exist_ok=True)
