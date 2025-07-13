from playwright.sync_api import sync_playwright
import requests
class progressConnector:
    def __init__(self, username, password, headless=True):
        self.username = username
        self.password = password
        self.browser = None
        self.page = None
        self.headless = headless
        self.playwright = sync_playwright().start()

    def login(self):
        initial_url = "https://progress.upatras.gr"

        
        self.browser = self.playwright.chromium.launch(headless=self.headless)  # headless mode
        self.page = self.browser.new_page()

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


        