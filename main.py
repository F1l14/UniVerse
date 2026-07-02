import asyncio
import os

# os.environ["FLAGS_use_mkldnn"] = "0"
# os.environ["FLAGS_enable_onednn_passes"] = "0"
# os.environ["FLAGS_enable_pir_in_executor"] = "0"
import subprocess
from eclass import EclassConnector
from progress import ProgressConnector
from user import User
from new_scheduler import Scheduler
import aioconsole  # async input for non-blocking menu


async def run_progress(username, password, headless=True, webhook_url=None):
    """Fetch grades from Progress with CAPTCHA handling."""
    from ocr import OCR
    from datetime import datetime
    
    start_time = datetime.now()
    progress = ProgressConnector(username, password, headless=headless, webhook_url=webhook_url)
    success = False
    
    try:
        await progress.start()
        await progress.login()

        for attempt in range(1, 6):
            print(f"--- CAPTCHA Attempt {attempt} ---")
            print("Fetching CAPTCHA image...")
            if not await progress.fetch_captcha_image(reload=(attempt > 1)):
                print("[XXX] Failed to fetch CAPTCHA image. Refreshing and trying again...")
                continue

            ocr = OCR()
            top_candidates = ocr.recognise_top_candidates("temp/captcha.png", max_count=3)
            
            try:
                os.remove("temp/captcha.png")
            except FileNotFoundError:
                pass

            if not top_candidates:
                print("No confident candidates found.")
                continue

            # Only try the top candidate (index 0) because any submission refreshes the CAPTCHA image
            candidate = top_candidates[0]
            print(f"Trying top candidate: {candidate}")
            await progress.verify_captcha(candidate)
            retry = await progress.get_grades()
            if not retry:
                success = True
                break
            else:
                print(f"Candidate {candidate} was incorrect. Retrying with new CAPTCHA...")

        if not success:
            print("[XXX] All captcha attempts failed after reloading.")
            if webhook_url:
                from notification import Notification
                Notification(webhook_url=webhook_url).notify(
                    title="UniVerse Error",
                    message="The grade checker failed to fetch your grades after 5 attempts."
                )
    except Exception as e:
        print(f"[XXX] Crash in run_progress: {e}")
        if webhook_url:
            from notification import Notification
            Notification(webhook_url=webhook_url).notify(
                title="UniVerse Crash",
                message=f"The grade checker crashed unexpectedly:\n`{str(e)}`"
            )
    finally:
        await progress.stop()
        end_time = datetime.now()
        
        stats = {
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round((end_time - start_time).total_seconds(), 2),
            "captcha_attempts": progress.captcha_counter,
            "grades_modified": getattr(progress, "grades_modified", False),
            "status": "success" if success else "failed"
        }
        
        return stats


async def run_eclass(username, password, headless=True):
    """Fetch and sync Eclass courses."""
    eclass = EclassConnector(username, password, headless=headless)
    await eclass.start()
    try:
        await eclass.login()
        # await eclass.fetch_courses()
        await eclass.sync_courses()
    finally:
        await eclass.stop()


def phone_handler(phone_id):
    """Send course and grades files to phone via KDE Connect."""
    def send_file(filepath):
        command = ["kdeconnect-cli", "--share", filepath, "-d", phone_id]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"Sent file: {filepath}")
        except subprocess.CalledProcessError as e:
            print(f"Error sending file {filepath}:")
            print(e.stderr)
            # Exit on failure as original code did
            raise SystemExit(1)

    files = ["data/courses.json", "data/grades.json"]
    for file_path in files:
        if os.path.exists(file_path):
            send_file(file_path)
    # Original code exited after sending; we keep that behavior
    raise SystemExit(0)


async def print_main_menu():
    """Display the main menu and return user choice asynchronously."""
    print("\n" + "=" * 40)
    print("          UniVerse Main Menu")
    print("=" * 40)
    print("1. Eclass - Access course materials")
    print("2. Progress - Check grades")
    print("3. Scheduler - Manage automated tasks")
    print("4. Spectate - Watch scheduler status")
    print("5. Phone - Send files to phone via KDE Connect")
    print("6. Debug - Test CAPTCHA reload button")
    print("0. Exit")
    print("-" * 40)
    choice = await aioconsole.ainput("Select an option (0-6): ")
    return choice.strip()


async def scheduler_menu(username, password, scheduler, webhook_url=None):
    """Async menu for scheduler management."""
    while True:
        print("\n" + "-" * 30)
        print("Scheduler Management")
        print("-" * 30)
        print("1. Add Job")
        print("2. Start Scheduler")
        print("3. Stop Scheduler")
        print("4. Back to Main Menu")
        choice = await aioconsole.ainput("Select an option (1-4): ")
        choice = choice.strip()

        if choice == '1':
            print("\nAvailable job functions:")
            print("1. Fetch grades from Progress")
            option = await aioconsole.ainput("Select job (1): ")
            if option.strip() == '1':
                job = run_progress
            else:
                print("Invalid option. Returning to scheduler menu.")
                continue

            interval_str = await aioconsole.ainput("Enter interval (minutes): ")
            try:
                interval = int(interval_str)
                if interval <= 0:
                    raise ValueError
            except ValueError:
                print("Please enter a positive integer for interval.")
                continue

            scheduler.add_job(job, interval, "minute", username, password, True, webhook_url)
            print(f"Job added: {job.__name__} every {interval} minute(s).")

        elif choice == '2':
            if not scheduler.tasks:
                print("No jobs added yet. Please add a job first.")
                continue
            print("Starting scheduler...")
            scheduler.running = True
            # Create a task to run the scheduler; we don't await it here to keep menu responsive
            asyncio.create_task(scheduler.start())
            print("Scheduler started in background.")

        elif choice == '3':
            if scheduler.running:
                print("Stopping scheduler...")
                scheduler.stop()
                print("Scheduler stopped.")
            else:
                print("Scheduler is not running.")

        elif choice == '4':
            print("Returning to main menu.")
            break

        else:
            print("Invalid choice. Please try again.")


async def debug_reload_button(username, password, webhook_url=None):
    """Debug utility to log in and test clicking the CAPTCHA reload button."""
    from progress import ProgressConnector
    progress = ProgressConnector(username, password, headless=False)
    await progress.start()
    await progress.login()
    
    print("[DEBUG] Fetching initial CAPTCHA image...")
    await progress.fetch_captcha_image(reload=False)
    await asyncio.sleep(15)
    
    for i in range(1, 4):
        print(f"[DEBUG] Clicking CAPTCHA reload button #{i} via fetch_captcha_image(reload=True)...")
        await progress.fetch_captcha_image(reload=True)
        await asyncio.sleep(15)
    
    print("[DEBUG] Sending test Discord notification...")
    from notification import Notification
    Notification(webhook_url=webhook_url).notify(
        title="UniVerse Debug Test",
        message="This is a test notification from the CAPTCHA reload debug menu choice 6! Your Webhook connection works!"
    )
    
    print("[DEBUG] Debug test completed successfully. Stopping browser...")
    await progress.stop()


async def main():
    """Main application entry point."""
    print("Initializing UniVerse...")
    user = User()
    username, password, phone_id, discord_webhook = user.login()
    print(f"Logged in as {username}")

    scheduler = Scheduler()

    while True:
        choice = await print_main_menu()

        if choice == '1':
            print("\nLaunching Eclass...")
            await run_eclass(username, password, headless=True)

        elif choice == '2':
            print("\nFetching Progress grades...")
            await run_progress(username, password, headless=False, webhook_url=discord_webhook)

        elif choice == '3':
            await scheduler_menu(username, password, scheduler, discord_webhook)

        elif choice == '4':
            print("\nSpectating scheduler status...")
            if not scheduler.running:
                print("Scheduler is not running.")
                continue
            print("Press Ctrl+C to stop spectating and return to menu.")
            try:
                while scheduler.running:
                    print(f"Scheduler is running... (active jobs: {len(scheduler.tasks)})")
                    await asyncio.sleep(10)
            except KeyboardInterrupt:
                print("\nStopped spectating.")

        elif choice == '5':
            print("\nSending files to phone via KDE Connect...")
            phone_handler(phone_id)
            # phone_handler calls SystemExit on success; if we reach here, something went wrong
            print("Phone handler finished.")

        elif choice == '6':
            print("\nRunning CAPTCHA reload debug test...")
            await debug_reload_button(username, password, discord_webhook)

        elif choice == '0':
            print("\nExiting UniVerse. Goodbye!")
            if scheduler.running:
                scheduler.stop()
            break

        else:
            print("Invalid option. Please enter a number between 0 and 6.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting gracefully.")