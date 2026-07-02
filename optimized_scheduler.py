import asyncio
import sys
import os
import json
from user import User
from main import run_progress

def save_metadata(job_name, stats):
    folder = "metadata"
    os.makedirs(folder, exist_ok=True)
    
    safe_job_name = "".join(c for c in job_name if c.isalnum() or c in ("_", "-"))
    filepath = os.path.join(folder, f"{safe_job_name}_stats.json")
    
    history = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception:
            history = []
            
    history.append(stats)
    
    if len(history) > 100:
        history = history[-100:]
        
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"Saved stats to {filepath}")
    except Exception as e:
        print(f"Failed to write stats to {filepath}: {e}")

def check_last_run_limit():
    filepath = "metadata/run_progress_stats.json"
    if not os.path.exists(filepath):
        return True
        
    # Default cooldown is 60 minutes
    cooldown_minutes = 60
    
    # Read interval from command-line argument if provided
    if len(sys.argv) > 1:
        try:
            # Try to see if the first arg is an integer representing interval in minutes
            param = int(sys.argv[1])
            if param < 60:
                print(f"[ERROR] The specified interval ({param} minutes) is below the 60-minute safety limit.")
                print("To prevent portal blocks, you cannot run checks more than once per hour.")
                sys.exit(1)
            cooldown_minutes = param
        except ValueError:
            # If the argument is not an integer (e.g. some other script parameters), ignore
            pass
            
    # Apply a 5-minute buffer to account for minor cron execution timing fluctuations
    cooldown_seconds = (cooldown_minutes * 60) - 300
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            history = json.load(f)
            if not history or not isinstance(history, list):
                return True
            
            last_run = history[-1]
            last_start_str = last_run.get("start_time")
            if not last_start_str:
                return True
                
            from datetime import datetime
            last_start = datetime.strptime(last_start_str, "%Y-%m-%d %H:%M:%S")
            time_elapsed = (datetime.now() - last_start).total_seconds()
            
            if time_elapsed < cooldown_seconds:
                minutes_left = int((cooldown_seconds - time_elapsed) // 60)
                print(f"[WARNING] Grade check skipped. A check was already run recently ({int(time_elapsed // 60)} minutes ago).")
                print(f"To avoid rate-limiting or IP bans, please wait at least {minutes_left} more minutes.")
                return False
    except Exception as e:
        print(f"[DEBUG] Error checking last run timestamp: {e}")
        
    return True

async def main():
    # Verify environment variable exists
    decrypt_pw = os.environ.get("DECRYPT_PASSWORD")
    if not decrypt_pw:
        print("[ERROR] DECRYPT_PASSWORD environment variable not set.")
        print("Please run with: DECRYPT_PASSWORD='your_password' python optimized_scheduler.py")
        sys.exit(1)
        
    # Enforce rate-limiting checks
    if not check_last_run_limit():
        sys.exit(0)
        
    try:
        user = User()
        username, password, phone_id, discord_webhook = user.login()
    except Exception as e:
        print(f"[ERROR] Failed to decrypt credentials: {e}")
        sys.exit(1)

    print(f"Logged in as {username}. Starting optimized grade check...")
    
    # Run the grade check headlessly
    result = await run_progress(username, password, headless=True, webhook_url=discord_webhook)
    if isinstance(result, dict) and "captcha_attempts" in result:
        save_metadata("run_progress", result)
        
    print("[OK] Grade check completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
