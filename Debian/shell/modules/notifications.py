from fabric.widgets.wayland import WaylandWindow as Window
from fabric.notifications import Notification
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.image import Image
from fabric.widgets.button import Button
from fabric.utils.helpers import truncate

from services.notifications import NotificationService
from util.helpers import get_app_icon_pixbuf
from util.ui import add_hover_cursor
import config.icons as Icons

from gi.repository import GLib


class NotificationsOverview(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="notifications-overview",
            spacing=20,
            orientation="v",
            v_expand=True,
            **kwargs,
        )

        self.notification_service = NotificationService.get_instance()

        self.notifications_list = Box(
            name="notifications-list",
            orientation="v",
            spacing=10,
            h_expand=True,
            v_expand=True,
        )
        self.notifications_view = ScrolledWindow(
            name="notifications-view",
            h_expand=True,
            v_expand=True,
            child=self.notifications_list,
        )

        self.children = [
            Label(
                label="Notifications",
            ),
            self.notifications_view,
        ]

        self.notification_service.connect(
            "notification-added", self.on_notification_added
        )

    def on_notification_added(self, notifications: NotificationService, id: int):
        notification = notifications.get_notification_from_id(id)
        notification_element = NotificationOverviewElement(notification)
        current_notifications = self.notifications_list.children
        current_notifications.insert(0, notification_element)
        self.notifications_list.children = current_notifications

        notification.connect(
            "closed", lambda *_: self.notifications_list.remove(notification_element)
        )


class NotificationOverviewElement(Box):
    def __init__(self, notification: Notification, **kwargs):
        super().__init__(
            style_classes="notification-overview-element",
            orientation="h",
            spacing=20,
            **kwargs,
        )

        app_icon_pixbuf = get_app_icon_pixbuf(notification.app_name, 50, 50)
        if app_icon_pixbuf is not None:
            app_icon = Image(
                pixbuf=app_icon_pixbuf,
            )
            self.add(app_icon)
        else:
            app_name = Label(
                style_classes="notification-overview-element-app-name",
                label=truncate(notification.app_name, 20),
            )
            self.add(app_name)

        summary = Label(
            h_expand=True,
            h_align="start",
            style_classes="notification-overview-element-summary",
            label=truncate(notification.summary, 50),
            line_wrap="char",
        )
        self.add(summary)

        close_button = Button(
            child=Label(
                style_classes="notification-overview-element-close-icon",
                markup=Icons.delete,
            ),
            on_clicked=lambda *_: notification.close(),
        )
        add_hover_cursor(close_button)
        self.add(close_button)


class NotificationPopUp(Window):
    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="bottom center",
            exclusivity="none",
            title="fabric-notifications-pop-up",
            margin="0px 0px 20px 0px",
            visible=False,
            **kwargs,
        )

        self.notification_service = NotificationService.get_instance()

        self.notifications_list = Box(
            orientation="v",
            spacing=40,
            h_expand=True,
            v_expand=True,
            name="notifications-pop-up-list",
        )

        self.children = self.notifications_list

        self.notification_service.connect(
            "notification-added", self.on_notification_added
        )

    def on_notification_added(self, notifications: NotificationService, id: int):
        if len(self.notifications_list.children) == 3:
            return

        notification = notifications.get_notification_from_id(id)
        notification_element = NotificationPopUpElement(notification)
        children = self.notifications_list.children
        children.insert(0, notification_element)
        self.notifications_list.children = children

        if not self.get_visible():
            self.show_all()

        GLib.timeout_add(
            2500 + 1000 * len(self.notifications_list.children),
            lambda: self.hide_notification_pop_up(notification_element),
        )

    def hide_notification_pop_up(self, notification_element):
        self.notifications_list.remove(notification_element)

        if self.notifications_list.children == []:
            self.hide()

        return False


class NotificationPopUpElement(Box):
    def __init__(self, notification: Notification, **kwargs):
        super().__init__(
            style_classes="notification-pop-up-element",
            orientation="v",
            h_align="center",
            spacing=20,
            **kwargs,
        )

        header = Box(
            spacing=20,
            orientation="h",
            h_align="center",
            v_align="center",
        )

        app_icon_pixbuf = get_app_icon_pixbuf(notification.app_name, 75, 75)
        if app_icon_pixbuf is not None:
            app_icon = Image(
                pixbuf=app_icon_pixbuf,
            )
            header.add(app_icon)
        else:
            app_name = Label(
                style_classes="notification-pop-up-element-app-name",
                label=truncate(notification.app_name, 20),
            )
            header.add(app_name)

        summary = Label(
            style_classes="notification-pop-up-element-summary",
            label=truncate(notification.summary, 50),
        )
        header.add(summary)

        self.add(header)

        image_pixbuf = notification.image_pixbuf

        if notification.body != "" or image_pixbuf is not None:
            body = Box(
                style_classes="notification-pop-up-element-body",
                spacing=20,
                orientation="h",
                v_align="center",
                h_align="center",
            )
            self.add(body)

        if image_pixbuf is not None:
            image = Image(
                style_classes="notification-pop-up-element-image",
                pixbuf=image_pixbuf,
                size=(100, 100),
            )
            body.add(image)

        if notification.body != "":
            body_text = Label(
                style_classes="notification-pop-up-element-body-text",
                markup=truncate(notification.body, 200),
                line_wrap="char",
                h_align="center",
                h_expand="True",
            )
            body.add(body_text)
