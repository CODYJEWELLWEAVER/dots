from typing import Literal
from gi.repository import Gdk
from fabric.widgets.shapes import Corner


def add_hover_cursor(widget):
    """
    Changes cursor when hovering over widget and resets when moving away from widget.
    Credit to https://github.com/Axenide for this.
    """
    widget.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
    widget.connect(
        "enter-notify-event",
        lambda w, event: w.get_window().set_cursor(
            Gdk.Cursor.new_from_name(Gdk.Display.get_default(), "pointer")
        ),
    )
    widget.connect(
        "leave-notify-event", lambda w, event: w.get_window().set_cursor(None)
    )


def toggle_visible(*widgets):
    """
    Show or hide widget based on current visibility.
    """
    for widget in widgets:
        is_visible = widget.get_visible()
        widget.set_visible(not is_visible)


def corner(position: Literal["left", "right"], size: Literal["small", "large"]):
    size = (225, 75) if size == "large" else (75, 25)
    if position == "left":
        orientation = "top-right"
        style_class = "left-corner"
    else:
        orientation = "top-left"
        style_class = "right-corner"
    return Corner(
        orientation=orientation,
        style_classes=style_class,
        size=size
    )