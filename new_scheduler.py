import asyncio

class Scheduler:
    def __init__(self):
        self.tasks = []
        self.running = False
    
    def add_job(self, coroutine_func, interval, fraction="hour", *args, **kwargs):
        if fraction == "minute":
            print("==== minutes ====")
            mult = 60
        else:
            mult = 3600
        
        time = interval * mult

        async def job_wrapper():
            while self.running:
                print(f"Running job: {coroutine_func.__name__}")
                await coroutine_func(*args, **kwargs)
                await asyncio.sleep(time)
        self.tasks.append(job_wrapper)

    async def start(self):
        print("Scheduler ON")
        self.running = True
        # runs all the job_wrapper functions concurrently
        await asyncio.gather(*(task() for task in self.tasks))
    
    def stop(self):
        self.running = False