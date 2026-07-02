import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="plyer.*")

from plyer import notification
import schedule
import time
import requests

class Notification:
    def __init__(self, app_name="UniVerse", webhook_url=None):
        self.app_name = app_name
        self.webhook_url = webhook_url

    def notify(self, title, message, timeout=5):
        # Local desktop notification
        try:
            notification.notify(
                app_name=self.app_name,
                title=title,
                message=message,
                timeout=timeout  # seconds
            )
        except Exception as e:
            print(f"Local notification warning: {e}")

        # Discord Webhook notification
        if self.webhook_url:
            self.send_to_discord(title, message)

    def send_to_discord(self, title, message):
        payload = {
            "embeds": [
                {
                    "title": f"🎓 {title}",
                    "description": message,
                    "color": 3066993,  # Green
                    "footer": {
                        "text": self.app_name
                    }
                }
            ]
        }
        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 204:
                print("[OK] Discord notification sent successfully.")
            else:
                print(f"[XXX] Discord webhook returned status: {response.status_code}")
        except Exception as e:
            print(f"[XXX] Failed to send Discord webhook: {e}")