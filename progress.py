from playwright.sync_api import sync_playwright
import requests
import os
from notification import Notification
class ProgressConnector:
    def __init__(self, username, password, headless=True):
        self.username = username
        self.password = password
        self.browser = None
        self.page = None
        self.headless = headless
        self.playwright = sync_playwright().start()

    def block_resources(self, route):
        request = route.request
        if request.resource_type in ["font"] or request.url.lower().endswith(('.jpg', '.jpeg', '.gif','.svg', '.pdf')): 
            route.abort()
        else:
            route.continue_()

    def login(self):
        initial_url = "https://progress.upatras.gr"

        
        self.browser = self.playwright.chromium.launch(headless=self.headless)  # headless mode
        self.context = self.browser.new_context()
        # *for all urls limit resoursces to reduce load time
        self.context.route("**/*", self.block_resources)
        self.page = self.context.new_page()

        # Step 1: Go to initial URL (login page or redirect)
        self.page.goto(initial_url)

        # Optional: wait for form to be visible
        self.page.wait_for_selector('form')

        # Step 2 & 3: Fill in the form inputs
        # You can fill inputs by their 'name' attributes:
        self.page.fill('input[name="j_username"]', self.username)
        self.page.fill('input[name="j_password"]', self.password)

        # The original form had a hidden field '_eventId_proceed' with value 'Σύνδεση'
        # If needed, fill it using evaluate or by setting hidden input if present
        # If it's not an input field, we might need to add it via JS or ignore

        # Step 4: Submit the form
        # You can click the submit button or use form.submit()

        # Try clicking the submit button - usually type="submit"
        self.page.click('button[type="submit"], input[type="submit"]')

        # Wait for navigation after form submission
        self.page.wait_for_load_state('networkidle')

        # Step 5: Check if login succeeded
        current_url = self.page.url
        page_content = self.page.content()

        print("Final URL:", current_url)

        if "eclass" in current_url or "logout" in page_content.lower():
            print("✅ Login successful")
        else:
            print("⚠️ Login may have failed")
            error = self.page.query_selector('.form-error')
            if error:
                print("Error message:", error.text_content())
            else:
                print("No specific error message found.")
        
        self.page.click("div[title='Ακαδημαϊκό Έργο']")
        self.page.wait_for_load_state('networkidle')


    def fetch_captcha_image(self):

        self.page.wait_for_load_state("networkidle")
        # ! FIXME: This is a workaround to ensure the page is fully loaded
        self.page.wait_for_timeout(4000)  # wait extra 3 sec

        # for frame in self.page.frames:
        #     print("📄 Frame:")
        #     print("  Name:", frame.name)
        #     print("  URL :", frame.url)

        iframe = self.page.frame(name="isolatedWorkArea")
        if not iframe:
            print("⚠️ No iframe found with id 'isolatedWorkArea'")
            return
        
        container = iframe.query_selector("div.lsHTMLContainer")
        image_elemet = container.query_selector("img[ct='IMG']")
        url = "https://matrix.upatras.gr/"
        img_url = url + image_elemet.get_attribute("src")
        response = requests.get(img_url)
        if response.status_code == 200:
            with open("temp/captcha.png", "wb") as f:
                f.write(response.content)
            print("✅ Captcha image saved as 'captcha.png'")
        else:
            print(f"⚠️ Failed to fetch captcha image, status code: {response.status_code}")

    def verify_captcha(self, captcha_text):
        iframe = self.page.frame(name="isolatedWorkArea")
        container = iframe.query_selector("div.lsHTMLContainer")
        input_element = container.query_selector("input[ct='I']")
        input_element.fill(captcha_text)
        iframe.locator("div.lsHTMLContainer div.lsButton[lsdata*='ΕΠΟΜΕΝΟ']").click()
        self.page.wait_for_load_state("networkidle")
        # ! FIXME: This is a workaround to ensure the page is fully loaded
        self.page.wait_for_timeout(4000)  # wait extra 3 sec

    def get_grades(self):
        
        iframe = self.page.frame(name="isolatedWorkArea")
        table = iframe.query_selector("table.urST3BdBrd")
        rows = table.query_selector_all("tbody tr[rt='1']")

        grades = {}
        # calculate the latest academic year to compare grades
        max_year = None
        for row in rows:
            
            cells = row.query_selector_all("td")
            if len(cells) < 8:
                continue
            semester = cells[0].text_content().strip()
            course = cells[3].text_content().strip()
            grade = cells[4].text_content().strip()
            year = cells[5].text_content().strip()
            # academic year is in the format "YYYY-YY (e.g. 2024-25)"
            year= int(year.split("-")[0])
            
            if max_year is None or  year > max_year:
                max_year = year
            state = cells[7].text_content().strip()
            if state in ["Τελικό","Τελικό (Επαναληπτικές)"]:
                state = "final"
            elif state == "Προσωρινό":
                state = "temporary"
            else:
                state = "unknown"

            #append to dictionary
            if semester not in grades:
                grades[semester] = {}

            if course in grades[semester]:
                # if the course exists , skip it
                continue
            
            grades[semester][course]={
                "grade": grade,
                "state": state,
                "year": year
            }

            # print(f"Semester: {semester}, Course: {course}, Grade: {grade}")

        # save grades to file
        self.compare_grades(grades, max_year)
        self.save_grades(grades)

    def compare_grades(self, grades, academic_year):
        import json
        if not os.path.exists("data/grades.json"):
            print("No previous grades found, saving current grades.")
            return
        
        with open("data/grades.json", "r", encoding="utf-8") as f:
            previous_grades = json.load(f)

        for semester, courses in grades.items():
            
            # check only the current academic year
            for course_name, details in courses.items():
                if details["year"] == academic_year:
                    if semester in previous_grades and course_name in previous_grades[semester]:
                        if previous_grades[semester][course_name]["state"] != details["state"] or previous_grades[semester][course_name]["grade"] != details["grade"]:
                                    Notification().notify(
                                        title="Νέος Βαθμός",
                                        message=f"{course_name}\n Βαθμός: {details['grade']}",
                                        timeout=0
                                    )
    def save_grades(self, grades):
        import json
        with open("data/grades.json", "w", encoding="utf-8") as f:
            json.dump(grades, f, ensure_ascii=False, indent=2)
        print("Grades saved to data/grades.json")