import threading
import schedule
import time

class Scheduler:
    def __init__(self):
        self.jobs = []
        # shared resource lock
        self.lock = threading.Lock()

    def add_job(self, job_func, interval):
        with self.lock:
            job = schedule.every(interval).minutes.do(job_func)
            self.jobs.append(job)
            print(f"Job added: {job_func.__name__} every {interval} hours")

    def run_pending(self):
        while True:
            with self.lock:
                schedule.run_pending()
            time.sleep(1)  # Sleep to avoid busy waiting
    
    def start(self):
        self.thread = threading.Thread(target=self.run_pending, daemon=True)
        self.thread.start()
        print("🚀 Scheduler started in background thread.")

    def stop(self):
        self._stop_event.set()
        self.thread.join()
        print("🛑 Scheduler stopped.")