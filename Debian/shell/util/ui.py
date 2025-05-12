from gi.repository import Gdk


def add_hover_cursor(widget):
    """
    Changes cursor when hovering over widget and resets when moving away from widget.
    """
    widget.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
    widget.connect("enter-notify-event", lambda w, event: w.get_window().set_cursor(
        Gdk.Cursor.new_from_name(Gdk.Display.get_default(), "pointer")))
    widget.connect("leave-notify-event", lambda w, event: w.get_window().set_cursor(None))


def toggle_visible(widget):
    """
    Show or hide widget based on current visibility.
    """
    is_visible = widget.get_visible()
    widget.set_visible(not is_visible)


def add_auto_close(widget):
    """
    Hides widget when keyboard-focus leaves window.
    """
    widget.add_events(Gdk.EventMask.FOCUS_CHANGE_MASK)
    widget.connect("focus-out-event", lambda w, event: w.set_visible(False))