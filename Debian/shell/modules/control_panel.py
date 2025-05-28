from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.eventbox import EventBox
from fabric.widgets.shapes.corner import Corner


class ControlPanel(Window):
    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            title="fabric-control-panel",
            name="control-panel",
            anchor="top center",
            exclusivity="none",
            margin="-60px 0px 0px 0px",
            visible=False,
            kwargs=kwargs    
        )


        self.content_box = Box(
            children=[
                Corner(
                    "top-right",
                    name="control-panel-left-corner",
                    size=(225, 75)
                ),
                Box(
                    name="control-panel-box",
                    children=Label(label="Placeholder.")
                ),
                Corner(
                    "top-left",
                    name="control-panel-left-corner",
                    size=(225, 75)
                ),
            ]
        )


        self.event_box = EventBox(
            events="leave-notify",
            child=self.content_box,
            name="control-panel-event-box"
        )


        self.event_box.connect("leave-notify-event", lambda *_: self.hide())


        self.children = self.event_box