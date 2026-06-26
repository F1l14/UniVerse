from plyer import notification
import schedule
import time

class Notification:
    def __init__(self, app_name="UniVerse"):
        self.app_name = app_name

    def notify(self, title, message, timeout=5):
        notification.notify(
            app_name=self.app_name,
            title=title,
            message=message,
            timeout=timeout  # seconds
        )