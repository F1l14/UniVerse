from playwright.async_api import async_playwright
import requests
import os
import asyncio
from notification import Notification

class ProgressConnector:
    def __init__(self, username, password, headless=True, webhook_url=None):
        self.username = username
        self.password = password
        self.browser = None
        self.page = None
        self.headless = headless
        self.captcha_counter = 0
        self.grades_modified = False
        self.webhook_url = webhook_url
        
    async def start(self):
        self.playwright = await async_playwright().start()


    async def stop(self):
        if self.browser is not None:
            try:
                await self.browser.close()
            except Exception:
                pass
            finally:
                self.browser = None

        if hasattr(self, "playwright") and self.playwright is not None:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            finally:
                self.playwright = None

    async def block_resources(self, route):
        request = route.request
        if request.resource_type in ["font"] or request.url.lower().endswith(('.jpg', '.jpeg', '.gif','.svg', '.pdf')): 
            await route.abort()
        else:
            await route.continue_()

    async def wait_for_idle(self, timeout=5000):
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass

    async def login(self):
        initial_url = "https://progress.upatras.gr"
        
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        await self.context.route("**/*", self.block_resources)
        self.page = await self.context.new_page()
        self.page.on("dialog", lambda dialog: asyncio.create_task(dialog.dismiss()))

        await self.page.goto(initial_url)
        await self.page.wait_for_selector('form')
        await self.page.fill('input[name="j_username"]', self.username)
        await self.page.fill('input[name="j_password"]', self.password)
        await self.page.click('button[type="submit"], input[type="submit"]')
        await self.wait_for_idle()

        current_url = self.page.url
        page_content = await self.page.content()

        print("Final URL:", current_url)

        if "eclass" in current_url or "logout" in page_content.lower():
            print("[OK] Login successful")
        else:
            print("[XXX] Login may have failed")
            error = await self.page.query_selector('.form-error')
            if error:
                print("Error message:", await error.text_content())
            else:
                print("No specific error message found.")
        
        menu_btn = await self.page.wait_for_selector("div[title='Ακαδημαϊκό Έργο']", state="visible", timeout=15000)
        # Wait 2 seconds to ensure event listeners are attached
        await self.page.wait_for_timeout(2000)
        await menu_btn.click()
        await self.wait_for_idle()

    async def fetch_captcha_image(self, reload=False):
        await self.wait_for_idle()

        # Wait for the iframe to load and ensure it is not detached
        iframe = None
        for _ in range(20):
            iframe = self.page.frame(name="isolatedWorkArea")
            if iframe and not iframe.is_detached():
                break
            await self.page.wait_for_timeout(500)

        if not iframe:
            print("[DEBUG] isolatedWorkArea iframe not found initially. Clicking menu button again...")
            # Try to click the menu button to load the iframe if it's not present
            menu_btn = await self.page.query_selector("div[title='Ακαδημαϊκό Έργο']")
            if menu_btn:
                await menu_btn.click()
                await self.wait_for_idle()
                try:
                    await self.page.wait_for_selector("iframe[name='isolatedWorkArea']", timeout=10000)
                except Exception:
                    pass
                for _ in range(10):
                    iframe = self.page.frame(name="isolatedWorkArea")
                    if iframe and not iframe.is_detached():
                        break
                    await self.page.wait_for_timeout(500)

        if not iframe:
            print("[XXX] No iframe found with id 'isolatedWorkArea'")
            return False

        # Wait up to 10 seconds for the CAPTCHA image element to load inside the iframe
        for attempt_idx in range(3):
            try:
                await iframe.wait_for_selector("img[ct='IMG']", state="visible", timeout=5000)
                break
            except Exception as e:
                if "detached" in str(e).lower() or "detached" in repr(e).lower():
                    print("[DEBUG] Frame was detached while waiting for CAPTCHA image. Re-acquiring frame...")
                    iframe = None
                    for _ in range(10):
                        await self.page.wait_for_timeout(500)
                        iframe = self.page.frame(name="isolatedWorkArea")
                        if iframe and not iframe.is_detached():
                            break
                    if not iframe:
                        print("[XXX] Failed to re-acquire isolatedWorkArea iframe.")
                        return False
                else:
                    print(f"[XXX] Warning: CAPTCHA image not visible in iframe: {e}")
                    break

        # Get old src if we are reloading
        old_src = None
        if reload:
            image_element = await iframe.query_selector("img[ct='IMG']")
            if image_element:
                old_src = await image_element.get_attribute("src")

        if reload:
            print("Clicking CAPTCHA reload button next to the image...")
            reload_button = await iframe.query_selector("div.lsButton[title*='Ανανέωση'], div.lsButton[title*='Refresh']")
            if reload_button:
                await reload_button.click()
                # Wait 1.5 seconds for the click to trigger and portal to start loading
                await self.page.wait_for_timeout(1500)
                
                # Wait for the src attribute to change
                if old_src:
                    print("Waiting for CAPTCHA image src attribute to change...")
                    src_changed = False
                    # Poll every 500ms for up to 40 attempts (20 seconds total)
                    for attempt in range(40):
                        await self.page.wait_for_timeout(500)
                        
                        # Re-acquire handles since reload destroys/detaches them
                        iframe = self.page.frame(name="isolatedWorkArea")
                        if not iframe or iframe.is_detached():
                            continue
                        
                        current_img = await iframe.query_selector("img[ct='IMG']")
                        if current_img:
                            current_src = await current_img.get_attribute("src")
                            if current_src and current_src != old_src:
                                print(f"CAPTCHA source changed successfully (Attempt {attempt+1})!")
                                src_changed = True
                                # Wait an extra 2.0 seconds for the new image asset to finish loading
                                await self.page.wait_for_timeout(2000)
                                break
                    if not src_changed:
                        print("[XXX] Warning: CAPTCHA source did not change. Waiting full 15s...")
                        await self.page.wait_for_timeout(15000)
                else:
                    await self.page.wait_for_timeout(15000)
            else:
                print("[XXX] CAPTCHA reload button not found. Waiting up to 60 seconds for the image to load instead of refreshing...")
                image_loaded = False
                for _ in range(60):
                    await self.page.wait_for_timeout(1000)
                    iframe = self.page.frame(name="isolatedWorkArea")
                    if iframe and not iframe.is_detached():
                        try:
                            img = await iframe.query_selector("img[ct='IMG']")
                            if img:
                                image_loaded = True
                                break
                        except Exception:
                            pass
                if not image_loaded:
                    print("[XXX] Image did not load after 60 seconds. Quitting attempt.")
                    return False

        # Re-acquire DOM elements to get the fresh references after reload/wait
        iframe = None
        for _ in range(10):
            iframe = self.page.frame(name="isolatedWorkArea")
            if iframe and not iframe.is_detached():
                break
            await self.page.wait_for_timeout(500)

        if not iframe:
            print("[XXX] No iframe found with id 'isolatedWorkArea' after reload/wait")
            return False

        # Wait up to 10 seconds for the image element to be visible/stable
        for attempt_idx in range(3):
            try:
                await iframe.wait_for_selector("img[ct='IMG']", state="visible", timeout=5000)
                break
            except Exception as e:
                if "detached" in str(e).lower() or "detached" in repr(e).lower():
                    print("[DEBUG] Frame was detached before screenshot. Re-acquiring...")
                    iframe = None
                    for _ in range(10):
                        await self.page.wait_for_timeout(500)
                        iframe = self.page.frame(name="isolatedWorkArea")
                        if iframe and not iframe.is_detached():
                            break
                else:
                    break

        image_element = await iframe.query_selector("img[ct='IMG']")
        if not image_element:
            print("[XXX] Image element 'img[ct=IMG]' not found after reload/wait")
            return False

        # Wait for the image to be fully loaded/decoded (img.complete && img.naturalWidth > 0)
        for _ in range(10):
            try:
                is_complete = await iframe.evaluate("img => img.complete && img.naturalWidth > 0", image_element)
                if is_complete:
                    break
            except Exception:
                pass
            await self.page.wait_for_timeout(500)

        # Try to screenshot the element directly (best sync with the browser viewport)
        try:
            os.makedirs("temp", exist_ok=True)
            await image_element.screenshot(path="temp/captcha.png")
            print("[OK] CAPTCHA image screenshot saved successfully.")
            return True
        except Exception as e:
            print(f"[XXX] Failed to screenshot CAPTCHA image element: {e}. Falling back to requests.get...")
            # Fallback to requests.get
            try:
                url = "https://matrix.upatras.gr/"
                img_url = url + await image_element.get_attribute("src")
                response = requests.get(img_url)
                if response.status_code == 200:
                    with open("temp/captcha.png", "wb") as f:
                        f.write(response.content)
                    print("[OK] CAPTCHA image fallback download saved successfully.")
                    return True
                else:
                    print(f"[XXX] Fallback requests.get failed, status code: {response.status_code}")
                    return False
            except Exception as e_fallback:
                print(f"[XXX] Fallback requests.get failed with error: {e_fallback}")
                return False

    async def verify_captcha(self, captcha_text):
        self.captcha_counter += 1
        iframe = self.page.frame(name="isolatedWorkArea")
        if not iframe:
            print("[XXX] No iframe found in verify_captcha")
            return

        try:
            # Wait for the input element to be visible
            await iframe.wait_for_selector("input[ct='I']", timeout=10000)
            input_element = await iframe.query_selector("input[ct='I']")
            if input_element:
                await input_element.fill(captcha_text)
                submit_btn = await iframe.query_selector("div.lsButton[lsdata*='ΕΠΟΜΕΝΟ']")
                if submit_btn:
                    await submit_btn.click()
                else:
                    await iframe.locator("div.lsButton[lsdata*='ΕΠΟΜΕΝΟ']").click()
                await self.wait_for_idle()
            else:
                print("[XXX] input_element was None in verify_captcha after waiting")
        except Exception as e:
            print(f"[XXX] Error in verify_captcha: {e}")

    async def get_grades(self):
        iframe = self.page.frame(name="isolatedWorkArea")
        if not iframe:
            return True
        try:
            # Wait up to 30 seconds for the grades table to load (portal can be very slow)
            await iframe.wait_for_selector("table.urST3BdBrd", timeout=30000)
            table = await iframe.query_selector("table.urST3BdBrd")
            rows = await table.query_selector_all("tbody tr[rt='1']")
        except Exception as e:
            print("[XXX] Retrying captcha...")
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
            data = json.load(f)
            previous_grades = data.get("grades", data)

        for semester, courses in grades.items():
            
            # check only the current academic year
            for course_name, details in courses.items():
                if details["year"] == academic_year:
                    if semester in previous_grades and course_name in previous_grades[semester]:
                        if previous_grades[semester][course_name]["state"] != details["state"]:
                            Notification(webhook_url=self.webhook_url).notify(
                                title="Νέα Κατάσταση",
                                message=f"{course_name}\n Κατάσταση: {details['state']}",
                                timeout=0
                            )
                            self.grades_modified = True
                        if previous_grades[semester][course_name]["grade"] != details["grade"]:
                            Notification(webhook_url=self.webhook_url).notify(
                                title="Νέος Βαθμός",
                                message=f"{course_name}\n Βαθμός: {details['grade']}",
                                timeout=0
                            )
                            self.grades_modified = True
                    else:
                        self.grades_modified = True


    def save_grades(self, grades):
        import json
        from datetime import datetime
        data_to_save = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "grades": grades
        }
        with open("data/grades.json", "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        print("Grades saved to data/grades.json")
