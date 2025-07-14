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

# def job():

#     notification.notify(
#         app_name="UniVerse",
#         title="You have a new grade",
#         message="This is a system notification",
#         timeout=5  # seconds
#     )

# schedule.every(10).seconds.do(job)
# while True:
#     schedule.run_pending()
#     time.sleep(1)