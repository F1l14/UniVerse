from eclass import EclassConnector
from progress import ProgressConnector
from user import User
from new_scheduler import Scheduler

import os
import time
import asyncio

async def run_progress(username, password, headless=True):
    from ocr import OCR
    retry = True
    retry_counter = 0
    progress = ProgressConnector(username, password, headless=headless)
    await progress.start()
    await progress.login()
    while retry:
        if retry_counter > 5:
            print("❌ Too many retries, exiting...")
            break
        
        # reload the image only after the first attempt
        reload = retry_counter > 1
        retry_counter += 1
        while(not await progress.fetch_captcha_image(reload = reload)):
            print("fetching image...")
        ocr = OCR()
        ocr.preprocess("temp/captcha.png")
        result = ocr.recognise_text("output/processed.png")
        print("main result:", result)
        os.remove("temp/captcha.png")
        await progress.verify_captcha(result)
        retry = await progress.get_grades()

    await progress.stop()

def run_eclass(username, password, headless=True):
    eclass = EclassConnector(username, password, headless=headless)
    eclass.login()
    # eclass.fetch_courses()
    eclass.sync_courses()


scheduler = None
async def main():

    
    async def scheduler_menu():
        print("Scheduler Menu:")
        print("1. Add Job")
        print("2. Start Scheduler")
        print("3. Stop Scheduler")
        print("4. Exit")
        
        global scheduler
        if scheduler is None:
            scheduler = Scheduler()
            print("Scheduler initialized.")
        else:
            print("Scheduler already initialized.")
        
        choice = input("Choose an option (1/2/3/4): ")
        if choice == '1':
            print("Available job functions: 1. fetch_grades")
            option = input("1/2/3: ")
            if option == '1':
                job = run_progress
            else:
                print("Invalid option, returning to menu.")
                return
            
            interval = int(input("Enter interval: "))
            
            scheduler.add_job(job, interval, "minute", username, password, False)
        
        elif choice == '2':
        #    avoid system blocking on scheduler infinite loop
            scheduler.running = True
            asyncio.create_task(scheduler.start()) 
        elif choice == '3':
            scheduler.stop()
        elif choice == '4':
            print("Exiting Scheduler Menu.")
            return

    user = User()
    username, password = user.login()
    print(f"Logged in as {username}")
    while(True):
        print("Options:\n1. Eclass\n2. Progress\n3. Scheduler \n4. Exit\n5. Spectate")
        choice = input("Choose an option (1/2/3/4): ")
        if choice == '1':
            run_eclass(username, password, headless=True)
        elif choice == '2':
            await run_progress(username, password, headless= False)
        elif choice == '3':
            await scheduler_menu()

        elif choice == '4':
            print("Exiting...")
            break
        elif choice == '5':
            await asyncio.sleep(10)
            while scheduler.running:
                print("Scheduler is running...")
                await asyncio.sleep(10)   
           
            print("Scheduler OFF")
        else:
            print("Invalid choice. Exiting...")


if __name__ == "__main__":
    asyncio.run(main())
