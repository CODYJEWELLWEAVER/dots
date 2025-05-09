from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.box import Box
from fabric.widgets.container import Container

from util.ui import add_hover_cursor

class PowerMenu(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="power-menu",
            anchor="top right",
            layer="overlay",
            exclusivity="none",
            visible=False,
            margin='5px 20px 0px 0px',
            size=(300,300),
            **kwargs
        )

        self.box = Box(
            name="power-menu-box",
            orientation="v",
        )

        self.power_label = Label(
            label="Power Off",
            style_classes="power-menu-label"
        )
        self.power_button = Button(
            child=self.power_label,
            style_classes="power-menu-button",
        )

        self.reboot_label = Label(
            label="Reboot",
            style_classes="power-menu-label"
        )
        self.reboot_button = Button(
            child=self.reboot_label,
            style_classes="power-menu-button"
        )

        self.lock_label = Label(
            label="Lock",
            style_classes="power-menu-label",
        )
        self.lock_button = Button(
            child=self.lock_label,
            style_classes="power-menu-button",
            h_expand=True,
            v_expand=True,
        )

        add_hover_cursor(self.power_button)
        add_hover_cursor(self.reboot_button)
        add_hover_cursor(self.lock_button)

        self.box.children = [
            self.power_button,
            self.reboot_button,
            self.lock_button
        ]

        self.children = self.box
