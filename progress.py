from playwright.async_api import async_playwright
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
        self.captcha_counter = 0
        
    async def start(self):
        self.playwright = await async_playwright().start()


    async def stop(self):
        await self.browser.close()
        await self.playwright.stop()

    async def block_resources(self, route):
        request = route.request
        if request.resource_type in ["font"] or request.url.lower().endswith(('.jpg', '.jpeg', '.gif','.svg', '.pdf')): 
            await route.abort()
        else:
            await route.continue_()

    async def login(self):
        initial_url = "https://progress.upatras.gr"
        
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        await self.context.route("**/*", self.block_resources)
        self.page = await self.context.new_page()

        await self.page.goto(initial_url)
        await self.page.wait_for_selector('form')
        await self.page.fill('input[name="j_username"]', self.username)
        await self.page.fill('input[name="j_password"]', self.password)
        await self.page.click('button[type="submit"], input[type="submit"]')
        await self.page.wait_for_load_state('networkidle')

        current_url = self.page.url
        page_content = await self.page.content()

        print("Final URL:", current_url)

        if "eclass" in current_url or "logout" in page_content.lower():
            print("✅ Login successful")
        else:
            print("⚠️ Login may have failed")
            error = await self.page.query_selector('.form-error')
            if error:
                print("Error message:", await error.text_content())
            else:
                print("No specific error message found.")
        
        await self.page.click("div[title='Ακαδημαϊκό Έργο']")
        await self.page.wait_for_load_state('networkidle')

    async def fetch_captcha_image(self, reload=False):
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(4000)  # wait extra 4 sec

        iframe = self.page.frame(name="isolatedWorkArea")
        if not iframe:
            print("⚠️ No iframe found with id 'isolatedWorkArea'")
            return False
        
        container = await iframe.query_selector("div.lsHTMLContainer")
        if reload:
            reload_button = await container.query_selector("div.lsButton[title*='Ανανέωση']")
            if reload_button:
                await reload_button.click()
                await self.page.wait_for_timeout(2000)
            else:
                print("⚠️ Reload button not found.")
                return False

        image_element = await container.query_selector("img[ct='IMG']")
        url = "https://matrix.upatras.gr/"
        img_url = url + await image_element.get_attribute("src")
        response = requests.get(img_url)
        if response.status_code == 200:
            os.makedirs("temp", exist_ok=True)
            with open("temp/captcha.png", "wb") as f:
                f.write(response.content)
            print("✅ Captcha image saved as 'captcha.png'")
            return True
        else:
            print(f"⚠️ Failed to fetch captcha image, status code: {response.status_code}")
            return False

    async def verify_captcha(self, captcha_text):
        iframe = self.page.frame(name="isolatedWorkArea")
        container = await iframe.query_selector("div.lsHTMLContainer")
        input_element = await container.query_selector("input[ct='I']")
        await input_element.fill(captcha_text)
        await iframe.locator("div.lsHTMLContainer div.lsButton[lsdata*='ΕΠΟΜΕΝΟ']").click()
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(4000)

    async def get_grades(self):
        iframe = self.page.frame(name="isolatedWorkArea")
        table = await iframe.query_selector("table.urST3BdBrd")
        try:
            rows = await table.query_selector_all("tbody tr[rt='1']")
        except Exception as e:
            print("⚠️ Retrying captcha...")
            return True # retry captcha if table not found

        grades = {}
        max_year = None
        for row in rows:
            cells = await row.query_selector_all("td")
            if len(cells) < 8:
                continue
            semester = (await cells[0].text_content()).strip()
            course = (await cells[3].text_content()).strip()
            grade = (await cells[4].text_content()).strip()
            year = (await cells[5].text_content()).strip()
            year = int(year.split("-")[0])
            
            if max_year is None or year > max_year:
                max_year = year

            state = (await cells[7].text_content()).strip()
            if state in ["Τελικό","Τελικό (Επαναληπτικές)"]:
                state = "final"
            elif state == "Προσωρινό":
                state = "temporary"
            else:
                state = "unknown"

            if semester not in grades:
                grades[semester] = {}

            if course in grades[semester]:
                continue
            
            grades[semester][course] = {
                "grade": grade,
                "state": state,
                "year": year
            }

        self.compare_grades(grades, max_year)
        self.save_grades(grades)
        return False
    

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
