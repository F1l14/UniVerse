from playwright.sync_api import sync_playwright

class EclassConnector:
    def __init__(self, username, password, headless=True):
        self.username = username
        self.password = password
        self.browser = None
        self.page = None
        self.headless = headless
    def login(self):
        initial_url = "https://eclass.upatras.gr/secure"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)  # headless mode
            page = browser.new_page()

            # Step 1: Go to initial URL (login page or redirect)
            page.goto(initial_url)

            # Optional: wait for form to be visible
            page.wait_for_selector('form')

            # Step 2 & 3: Fill in the form inputs
            # You can fill inputs by their 'name' attributes:
            page.fill('input[name="j_username"]', self.username)
            page.fill('input[name="j_password"]', self.password)

            # The original form had a hidden field '_eventId_proceed' with value 'Σύνδεση'
            # If needed, fill it using evaluate or by setting hidden input if present
            # If it's not an input field, we might need to add it via JS or ignore

            # Step 4: Submit the form
            # You can click the submit button or use form.submit()

            # Try clicking the submit button - usually type="submit"
            page.click('button[type="submit"], input[type="submit"]')

            # Wait for navigation after form submission
            page.wait_for_load_state('networkidle')

            # Step 5: Check if login succeeded
            current_url = page.url
            page_content = page.content()

            print("Final URL:", current_url)

            if "eclass" in current_url or "logout" in page_content.lower():
                print("✅ Login successful")
            else:
                print("⚠️ Login may have failed")
                error = page.query_selector('.form-error')
                if error:
                    print("Error message:", error.text_content())
                else:
                    print("No specific error message found.")
            input("Press Enter to exit and close the browser")
