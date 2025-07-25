from eclass import EclassConnector
from progress import ProgressConnector
from user import User
from new_scheduler import Scheduler
import argparse
import os
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


# ======================================================
# import subprocess to run system commands
import subprocess
def phoneHandler(phone_id):
    command = ["kdeconnect-cli", "--ping","-d",  phone_id]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        print("PING! ", result.stdout)
        sendToPhone(phone_id)

    except subprocess.CalledProcessError as e:
        print("Error pinging device:")
        print("Device is not Connected...")
        # print(e.stderr)
        exit()

def sendToPhone(phone_id):
    def sendFile(filepath):
        command = ["kdeconnect-cli", "--share", filepath, "-d", phone_id]
        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            print("Sent file: ", filepath)

        except subprocess.CalledProcessError as e:
            print("Error sending file:", file)
            print(e.stderr)
            exit()
    
    files = ["data/courses.json", "data/grades.json"]
    for file in files:
        if os.path.exists(file):
            sendFile(file)
    exit()

    return None
# ======================================================

def argumentsHandler():
    parser = argparse.ArgumentParser()
    interval = None
    # store_true = false by default
    parser.add_argument("--scheduler", action="store_true", help="Specify the jobs for the scheduler")
    parser.add_argument("--all", action="store_true", help="Add all available jobs to the scheduler")
    parser.add_argument("--eclass", action="store_true", help="Add the eclass files job")
    parser.add_argument("--progress", action="store_true", help="Add the progress grades job")
    parser.add_argument("--ceid", action="store_true", help="Add the ceid news job")
    parser.add_argument("interval", help="The scheduler time interval in hours")
    args = parser.parse_args()
    if args.scheduler:
        if args.all:
            print("YESYESYES")
        if args.eclass:
            return
        if args.progress:
            return
        if args.ceid:
            return
        interval = args.interval
        print(interval)

    


scheduler = None
async def main():
    argumentsHandler()
    exit()
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
    username, password, phone_id = user.login()
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
        elif choice == "6":
            phoneHandler(phone_id)
        else:
            print("Invalid choice. Exiting...")


if __name__ == "__main__":
    asyncio.run(main())
