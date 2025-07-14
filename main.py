from eclass import EclassConnector
from progress import progressConnector
from user import User
from ocr import OCR
import os

def run_progress():
    progress = progressConnector(username, password, headless=False)
    progress.login()
    progress.fetch_captcha_image()
    ocr = OCR()
    ocr.preprocess("temp/captcha.png")
    result = ocr.recognise_text("output/processed.png")
    print("main result:", result)
    os.remove("temp/captcha.png")
    progress.verify_captcha(result)
    progress.get_grades()

def run_eclass():
    eclass = EclassConnector(username, password, headless=False)
    eclass.login()
    # eclass.fetch_courses()
    eclass.fetch_course_content("CEID1159")  # Example usage to fetch course content
    # eclass.fetch_course_content("course_id")  # Example usage to fetch course content



user = User()
username, password = user.login()

run_eclass()

input("Press Enter to exit...")


