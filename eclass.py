from playwright.async_api import async_playwright
from pathlib import Path
import os

class EclassConnector:
    def __init__(self, username, password, headless=True):
        self.username = username
        self.password = password
        self.browser = None
        self.page = None
        self.headless = headless
        self.documents_metadata = []

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
        # print(f"Resource type: {route.request.resource_type}, URL: {route.request.url}")
        # route.continue_()
        if request.resource_type in ["image", "font", "stylesheet"]:
            await route.abort()
        else:
            await route.continue_()

    async def login(self):
        initial_url = "https://eclass.upatras.gr/secure"

        self.browser = await self.playwright.chromium.launch(headless=self.headless)  # headless mode
        self.context = await self.browser.new_context()
        # *for all urls limit resoursces to reduce load time
        await self.context.route("**/*", self.block_resources)
        self.page = await self.context.new_page()

        # Step 1: Go to initial URL (login page or redirect)
        await self.page.goto(initial_url)

        # Optional: wait for form to be visible
        await self.page.wait_for_selector('form')

        # Step 2 & 3: Fill in the form inputs
        # You can fill inputs by their 'name' attributes:
        await self.page.fill('input[name="j_username"]', self.username)
        await self.page.fill('input[name="j_password"]', self.password)

        # Step 4: Submit the form
        await self.page.click('button[type="submit"], input[type="submit"]')

        # Wait for navigation after form submission
        await self.page.wait_for_load_state('networkidle')

        # Step 5: Check if login succeeded
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

    async def fetch_courses(self, store_courses=True):
        print("Fetching courses...")
        await self.page.goto("https://eclass.upatras.gr/main/my_courses.php")
        container_selector = "#MyCourses"
        try:
            await self.page.wait_for_selector(container_selector, timeout=5000)
        except Exception as e:
            print(f"Error waiting for container {container_selector}: {e}. Dumping page source to temp/my_courses_dump.html...")
            content = await self.page.content()
            os.makedirs("temp", exist_ok=True)
            with open("temp/my_courses_dump.html", "w", encoding="utf-8") as f:
                f.write(content)
            raise e
        courses = await self.page.query_selector_all("#MyCourses a.TextBold")
        for course in courses:
            print(await course.text_content())

        if store_courses:
            import json
            # Load existing sync preferences if file exists
            existing_sync = {}
            if os.path.exists("data/courses.json"):
                try:
                    with open("data/courses.json", "r", encoding="utf-8") as f:
                        old_list = json.load(f)
                        for c in old_list:
                            existing_sync[c["id"]] = c.get("sync", True)
                except Exception:
                    pass

            courses_list = []
            for course in courses:
                url = await course.get_attribute("href")
                name = await course.text_content()
                name = name.strip() if name else ""
                id = url.split("/")[-2] if url else ""
                # Keep existing sync preference if it exists, otherwise default to True
                sync_pref = existing_sync.get(id, True)
                courses_list.append({
                    "name": name,
                    "url": url,
                    "id": id,
                    "sync": sync_pref
                })
            
            with open("data/courses.json", "w", encoding="utf-8") as f:
                json.dump(courses_list, f, ensure_ascii=False, indent=2)
            print("Courses saved to courses.json")
    
    async def sync_courses(self):
        import json
        if not os.path.exists("data/courses.json"):
            await self.fetch_courses(store_courses=True)

        with open("data/courses.json", "r", encoding="utf-8") as f:
            courses = json.load(f)
        
        self.documents_metadata = []

        for course in courses:
            if course["sync"]:
                print(f"Syncing course: {course['name']}")
                await self.fetch_course_content(course["id"])
                
        # Save documents metadata to data/documents.json
        os.makedirs("data", exist_ok=True)
        with open("data/documents.json", "w", encoding="utf-8") as f:
            json.dump(self.documents_metadata, f, ensure_ascii=False, indent=2)
            
        print(f"Sync complete. Metadata for {len(self.documents_metadata)} items saved to data/documents.json")

    async def fetch_course_content(self, course_id, sub_dir=""):
        base_url = "https://eclass.upatras.gr"
        url = f"https://eclass.upatras.gr/modules/document/?course={course_id}"
        if sub_dir:
            url += f"&openDir={sub_dir}"
        
        await self.page.goto(url)
        await self.page.wait_for_load_state('networkidle')

        table = await self.page.query_selector("table")
        if not table:
            return
        
        rows = await table.query_selector_all("tbody tr")
        
        folders_to_process = []
        
        for row in rows:
            cells = await row.query_selector_all("td")
            if len(cells) > 1:
                link_el = await cells[1].query_selector("a")
                if not link_el:
                    continue
                name = await link_el.text_content()
                name = name.strip() if name else ""
                
                # Filter out parent directories to prevent infinite loops
                if name == ".." or "ανώτερος" in name.lower() or "parent" in name.lower():
                    continue

                href = await link_el.get_attribute("href") or ""
                is_folder = "openDir=" in href
                
                if href.startswith("http://") or href.startswith("https://"):
                    full_url = href
                elif href.startswith("//"):
                    full_url = "https:" + href
                else:
                    full_url = base_url + href

                logical_path = f"{sub_dir}/{name}" if sub_dir else f"/{name}"

                # Check for new badge (excluding the icon itself)
                spans = await cells[1].query_selector_all("span")
                has_new_content = False
                for s in spans:
                    txt = await s.text_content()
                    cls = await s.get_attribute("class")
                    if txt and ("νέο" in txt.lower() or "new" in txt.lower() or "label" in (cls or "") or "badge" in (cls or "")):
                        has_new_content = True
                        break

                if is_folder:
                    import urllib.parse
                    cleaned_href = href.replace("&amp;", "&")
                    parsed_url = urllib.parse.urlparse(cleaned_href)
                    params = urllib.parse.parse_qs(parsed_url.query)
                    dir_path = params.get("openDir", [""])[0]
                    
                    self.documents_metadata.append({
                        "course_id": course_id,
                        "name": name,
                        "path": logical_path,
                        "url": full_url,
                        "type": "folder",
                        "new": has_new_content
                    })
                    print("Found Folder:", logical_path)
                    
                    if dir_path:
                        folders_to_process.append((name, dir_path))
                else:
                    self.documents_metadata.append({
                        "course_id": course_id,
                        "name": name,
                        "path": logical_path,
                        "url": full_url,
                        "type": "file",
                        "new": has_new_content
                    })
                    print("Found File:", logical_path)

        # Recursively traverse sub-folders
        for folder_name, dir_path in folders_to_process:
            await self.fetch_course_content(course_id, sub_dir=dir_path)