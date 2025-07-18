from eclass import EclassConnector
from progress import ProgressConnector
from user import User

import os

def run_progress(headless):
    from ocr import OCR
    progress = ProgressConnector(username, password, headless=headless)
    progress.login()
    progress.fetch_captcha_image()
    ocr = OCR()
    ocr.preprocess("temp/captcha.png")
    result = ocr.recognise_text("output/processed.png")
    print("main result:", result)
    os.remove("temp/captcha.png")
    progress.verify_captcha(result)
    progress.get_grades()

def run_eclass(headless):
    eclass = EclassConnector(username, password, headless=headless)
    eclass.login()
    # eclass.fetch_courses()
    eclass.sync_courses()
    

user = User()
username, password = user.login()
print(f"Logged in as {username}")
print("Options:\n1. Eclass\n2. Progress\n3. Exit")
choice = input("Choose an option (1/2/3): ")
if choice == '1':
    run_eclass(headless=True)
elif choice == '2':
    run_progress(headless=True)
elif choice == '3':
    print("Exiting...")
else:
    print("Invalid choice. Exiting...")

# input("Press Enter to exit...")


