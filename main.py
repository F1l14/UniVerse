from eclass import EclassConnector
from progress import progressConnector
from user import User
from ocr import OCR
import os
user = User()
username, password = user.login()
# eclass = EclassConnector(username, password, headless=False)
# eclass.login()
# eclass.fetch_courses()

progress = progressConnector(username, password, headless=False)
progress.login()
progress.fetch_captcha_image()
ocr = OCR()
ocr.preprocess("temp/captcha.png")
result = ocr.recognise_text("output/processed.png")
print("main result:", result)
# os.remove("temp/captcha.png")


