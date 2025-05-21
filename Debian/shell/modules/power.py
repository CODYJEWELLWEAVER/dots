from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.box import Box
from fabric.widgets.image import Image
from fabric.widgets.revealer import Revealer
from fabric.utils import exec_shell_command

import config.icons as icons
from util.ui import add_hover_cursor, toggle_visible

from gi.repository import Gtk


"""
Module for displaying power options.
"""


class PowerControl(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="power-menu",
            anchor="right top",
            layer="top",
            exclusivity="normal",
            margin="10px 20px 0px 0px",
            keyboard_mode="on-demand",
            **kwargs
        )


        self.power_menu = PowerMenu()


        self.power_menu_toggle = Button(
            name="power-menu-toggle",
            child=Label(
                style_classes="power-menu-toggle-icon",
                markup=icons.power
            ),
            on_clicked=lambda *_: toggle_visible(self.power_menu)
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
            **kwargs
        )

        # Container for power options menu
        self.menu = Box(
            name="power-menu-box",
            orientation="v",
        )


        # dialogs for confirming reboot/suspend
        self.reboot_dialog = ConfirmationDialog(
            "Do you want to reboot?",
            self.reboot_system
        )
        self.suspend_dialog = ConfirmationDialog(
            "Do you want to suspend?",
            self.suspend_system
        )


        self.lock_button = Button(
            child=Label(
                style_classes="power-menu-icon",
                markup=icons.lock
            ),
            style_classes="power-menu-button",
            on_clicked=self.lock_screen
        )
        add_hover_cursor(self.lock_button)


        self.reboot_button = Button(
            child=Label(
                style_classes="power-menu-icon",
                markup=icons.reboot
            ),
            style_classes="power-menu-button",
            on_clicked=self.show_reboot_dialog
        )
        add_hover_cursor(self.reboot_button)


        #TODO: Add shutdown option
        self.suspend_button = Button(
            child=Label(
                style_classes="power-menu-icon",
                markup=icons.suspend
            ),
            style_classes="power-menu-button",
            on_clicked=self.show_suspend_dialog
        )
        add_hover_cursor(self.suspend_button)


        self.menu.children = [
            self.lock_button,
            self.reboot_button,
            self.suspend_button
        ]

        
        self.children = self.menu


    def show_reboot_dialog(self, *args):
        toggle_visible(self)
        self.suspend_dialog.set_visible(False) # close suspend dialog if open
        toggle_visible(self.reboot_dialog)


    def show_suspend_dialog(self, *args):
        toggle_visible(self)
        self.reboot_dialog.set_visible(False) # close reboot dialog if open
        toggle_visible(self.suspend_dialog)


    def lock_screen(self, *args):
        toggle_visible(self)
        exec_shell_command("loginctl lock-session")


    def reboot_system(self, *args):
        exec_shell_command("systemctl reboot")


    def suspend_system(self, *args):
        exec_shell_command("systemctl suspend")


class ConfirmationDialog(Window):
    """ Simple window to confirm action. """ 
    def __init__(self, prompt, action_callback, **kwargs):
        super().__init__(
            style_classes="confirm-dialog",
            layer="top",
            exclusivity="none",
            anchor="center",
            visible=False,
            kwargs=kwargs
        )


        # Container for dialog
        self.dialog = Box(
            orientation="v",
            style_classes="confirmation-menu"
        )


        # Dialog Prompt
        self.prompt_label = Label(
            prompt,
            style_classes="power-menu-label"
        )


        # Horizontal options container
        self.buttons_box = Box(
            orientation="h",
            h_align="center",
            v_align="center",
        )


        self.yes_label = Label(
            "Yes",
            style_classes="power-menu-label"
        )
        self.yes_button = Button(
            style_classes="confirmation-menu-button",
            child=self.yes_label,
            on_clicked=action_callback
        )
        add_hover_cursor(self.yes_button)


        self.no_label = Label(
            "No",
            style_classes="power-menu-label"
        )
        self.no_button = Button(
            style_classes="confirmation-menu-button",
            child=self.no_label,
            on_clicked=lambda *_: toggle_visible(self)
        )
        add_hover_cursor(self.no_button)


        self.buttons_box.children = [
            self.yes_button,
            self.no_button
        ]


        self.dialog.children = [
            self.prompt_label,
            self.buttons_box
        ]
        self.children = self.dialog 