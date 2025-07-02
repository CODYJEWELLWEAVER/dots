from util.singleton import Singleton
from fabric.notifications import Notifications, Notification

from gi.repository import GLib


class NotificationService(Notifications, Singleton):
    def send_internal_notification(self, variant: GLib.Variant):
        # add a notification internally and
        # emit the notification added signal
        id = self.new_notification_id()
        notification = Notification(id, variant)
        self._notifications[id] = notification
        self.notification_added(id)
