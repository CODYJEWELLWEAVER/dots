from fabric.widgets.wayland import WaylandWindow as Window

"""
Status bar for shell.
"""


class Bar(Window):
    def __init__(self, **kwargs):
        super().__init__(
            layer="top",
            anchor="left top right",
            exclusivity="none",
            **kwargs
        )