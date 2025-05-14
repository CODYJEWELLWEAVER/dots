from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.box import Box
from fabric.utils import exec_shell_command

from util.ui import add_hover_cursor, add_auto_close, toggle_visible


"""
Module for displaying power options.
"""


class PowerMenu(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="power-menu",
            anchor="top right",
            layer="top",
            exclusivity="none",
            keyboard_mode="on-demand",
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

        
        self.lock_label = Label(
            label="Lock",
            style_classes="power-menu-label",
        )
        self.lock_button = Button(
            child=self.lock_label,
            style_classes="power-menu-button",
            on_clicked=self.lock_screen
        )
        add_hover_cursor(self.lock_button)

        
        self.reboot_label = Label(
            label="Reboot",
            style_classes="power-menu-label"
        )
        self.reboot_button = Button(
            child=self.reboot_label,
            style_classes="power-menu-button",
            on_clicked=self.show_reboot_dialog
        )
        add_hover_cursor(self.reboot_button)

        
        self.suspend_label = Label(
            label="Suspend",
            style_classes="power-menu-label"
        )
        self.suspend_button = Button(
            child=self.suspend_label,
            style_classes="power-menu-button",
            on_clicked=self.show_suspend_dialog
        )
        add_hover_cursor(self.suspend_button)


        self.menu.children = [
            self.lock_button,
            self.reboot_button,
            self.suspend_button
        ]
        self.children = [
            self.menu, 
            self.reboot_dialog,
            self.suspend_dialog
        ]


        # close options menu when kb focus is lost
        add_auto_close(self)


    def show_reboot_dialog(self, *args):
        self.suspend_dialog.set_visible(False) # close suspend dialog if open
        toggle_visible(self.reboot_dialog)


    def show_suspend_dialog(self, *args):
        self.reboot_dialog.set_visible(False) # close reboot dialog if open
        toggle_visible(self.suspend_dialog)


    def lock_screen(self, *args):
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
            style_classes="power-menu-button",
            child=self.yes_label,
            on_clicked=action_callback
        )


        self.no_label = Label(
            "No",
            style_classes="power-menu-label"
        )
        self.no_button = Button(
            style_classes="power-menu-button",
            child=self.no_label,
            on_clicked=lambda *_: toggle_visible(self)
        )


        self.buttons_box.children = [
            self.yes_button,
            self.no_button
        ]


        add_hover_cursor(self.yes_button)
        add_hover_cursor(self.no_button)


        self.dialog.children = [
            self.prompt_label,
            self.buttons_box
        ]
        self.children = self.dialog