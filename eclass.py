from playwright.sync_api import sync_playwright

class EclassConnector:
    def __init__(self, username, password, headless=True):
        self.username = username
        self.password = password
        self.browser = None
        self.page = None
        self.headless = headless
        self.playwright = sync_playwright().start()
    def login(self):
        initial_url = "https://eclass.upatras.gr/secure"

        
        browser = self.playwright.chromium.launch(headless=self.headless)  # headless mode
        self.page = browser.new_page()

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
        # input("Press Enter to exit and close the browser")


    def fetch_courses(self, store_courses=True):
        
        print("Fetching courses...")
        self.page.goto("https://eclass.upatras.gr/main/my_courses.php")
        table_selector = "table"
        self.page.wait_for_selector(table_selector)
        courses = self.page.query_selector_all(f"{table_selector} tbody tr td:first-child a")
        for course in courses:
            print(course.text_content())
            # print(course.text_content() + " - " + course.get_attribute("href"))

        if store_courses:
            import json
            courses_list = []
            for course in courses:
                courses_list.append({
                    "name": course.text_content(),
                    "url": course.get_attribute("href")
                })
            
            with open("/data/courses.json", "w", encoding="utf-8") as f:
                json.dump(courses_list, f, ensure_ascii=False, indent=2)
            print("Courses saved to courses.txt")
        
    def fetch_course_content(self, course_id):
        self.page.goto(f"https://eclass.upatras.gr/modules/document/?course={course_id}")
        self.page.wait_for_load_state('networkidle')
        table = self.page.query_selector("table")
        rows = table.query_selector_all("tbody tr")

        def folder_handler(cells):
            print("Folder:", cells[2].text_content())
            return
        
        def file_handler(cells):
            print("File:", cells[2].text_content())
            return None
        
        for row in rows:
            # print(row.text_content())
            cells = row.query_selector_all("td")
            if len(cells) > 0:
                type = cells[1].query_selector("span").get_attribute("class")
                if "fa-folder" in type:
                    folder_handler(cells)
                else:
                    file_handler(cells)
            # new_content = cells[1].locator("span").count()> 0
            # if new_content:
            #     print("New content found in folder:", cells[0].text_content())