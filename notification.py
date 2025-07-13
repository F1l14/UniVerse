from plyer import notification
import schedule
import time

def job():

    notification.notify(
        app_name="UniVerse",
        title="You have a new grade",
        message="This is a system notification",
        timeout=5  # seconds
    )

schedule.every(10).seconds.do(job)
while True:
    schedule.run_pending()
    time.sleep(1)