from gi.repository import Gdk

def add_hover_cursor(widget):
    widget.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
    widget.connect("enter-notify-event", lambda w, event: w.get_window().set_cursor(
        Gdk.Cursor.new_from_name(Gdk.Display.get_default(), "pointer")))
    widget.connect("leave-notify-event", lambda w, event: w.get_window().set_cursor(None))

def toggle_visibility(widget):
        is_visible = widget.get_visible()
        widget.set_visible(not is_visible)