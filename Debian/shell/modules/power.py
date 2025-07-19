from typing import Callable
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.box import Box
from fabric.utils import exec_shell_command

import config.icons as Icons
from util.ui import add_hover_cursor, toggle_visible


"""
Module for displaying power options.
"""


class PowerControl(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="power-menu",
            h_align="center",
            v_align="center",
            v_expand=True,
            h_expand=True,
            keyboard_mode="on-demand",
            **kwargs,
        )

        self.power_menu = PowerMenu()

        self.power_menu_toggle = Button(
            name="power-menu-toggle",
            child=Label(style_classes="power-menu-toggle-icon", markup=Icons.power),
            on_clicked=lambda *_: toggle_visible(self.power_menu),
        )
        add_hover_cursor(self.power_menu_toggle)

        self.children = self.power_menu_toggle


class PowerMenu(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="power-menu",
            anchor="right top",
            layer="top",
            exclusivity="none",
            visible=False,
            **kwargs,
        )

        # Container for power options menu
        self.menu = Box(
            name="power-menu-box",
            orientation="v",
        )

        self.power_dialog = None

        self.lock_button = Button(
            child=Label(style_classes="power-menu-icon", markup=Icons.lock),
            style_classes="power-menu-button",
            on_clicked=self.lock_screen,
        )
        add_hover_cursor(self.lock_button)

        self.reboot_button = Button(
            child=Label(style_classes="power-menu-icon", markup=Icons.reboot),
            style_classes="power-menu-button",
            on_clicked=self.show_reboot_dialog,
        )
        add_hover_cursor(self.reboot_button)

        self.suspend_button = Button(
            child=Label(style_classes="power-menu-icon", markup=Icons.suspend),
            style_classes="power-menu-button",
            on_clicked=self.show_suspend_dialog,
        )
        add_hover_cursor(self.suspend_button)

        self.power_off_button = Button(
            child=Label(style_classes="power-menu-icon", markup=Icons.power_off),
            style_classes="power-menu-button",
            on_clicked=self.show_shutdown_dialog,
        )
        add_hover_cursor(self.power_off_button)

        self.menu.children = [
            self.lock_button,
            self.reboot_button,
            self.suspend_button,
            self.power_off_button,
        ]

        self.children = self.menu

    def destroy_dialog(self, *args):
        if self.power_dialog is not None:
            self.power_dialog.hide()
            self.power_dialog = None

    def show_reboot_dialog(self, *args):
        self.destroy_dialog()

        self.power_dialog = ConfirmationDialogRefactor(
            prompt="Do you want to reboot?",
            yes_callback=self.reboot_system,
            no_callback=self.destroy_dialog,
        )

        self.power_dialog.show()

    def show_suspend_dialog(self, *args):
        self.destroy_dialog()

        self.power_dialog = ConfirmationDialogRefactor(
            prompt="Do you want to suspend?",
            yes_callback=self.suspend_system,
            no_callback=self.destroy_dialog,
        )

        self.power_dialog.show()

    def show_shutdown_dialog(self, *args):
        self.destroy_dialog()

        self.power_dialog = ConfirmationDialogRefactor(
            prompt="Do you want to power off?",
            yes_callback=self.shutdown_system,
            no_callback=self.destroy_dialog,
        )

        self.power_dialog.show()

    def lock_screen(self, *args):
        toggle_visible(self)
        exec_shell_command("loginctl lock-session")

    def reboot_system(self, *args):
        exec_shell_command("systemctl reboot")

    def suspend_system(self, *args):
        exec_shell_command("systemctl suspend")

    def shutdown_system(self, *args):
        exec_shell_command("systemctl poweroff")


class ConfirmationDialogRefactor(Window):
    """Simple window to confirm action."""

    def __init__(self, prompt, yes_callback: Callable, no_callback: Callable, **kwargs):
        super().__init__(
            style_classes="confirm-dialog",
            layer="top",
            exclusivity="none",
            anchor="center",
            visible=False,
            kwargs=kwargs,
        )

        # Container for dialog
        self.dialog = Box(orientation="v", style_classes="confirmation-menu")

        # Dialog Prompt
        self.prompt_label = Label(prompt, style_classes="power-menu-label")

        # Horizontal options container
        self.buttons_box = Box(
            orientation="h",
            h_align="center",
            v_align="center",
        )

        self.yes_button = Button(
            style_classes="confirmation-menu-button",
            child=Label("Yes", style_classes="power-menu-label"),
            on_clicked=yes_callback,
        )
        add_hover_cursor(self.yes_button)

        self.no_button = Button(
            style_classes="confirmation-menu-button",
            child=Label("No", style_classes="power-menu-label"),
            on_clicked=no_callback,
        )
        add_hover_cursor(self.no_button)

        self.buttons_box.children = [self.yes_button, self.no_button]

        self.dialog.children = [self.prompt_label, self.buttons_box]
        self.children = self.dialog
