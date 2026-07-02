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

async def main():
    # Verify environment variable exists
    decrypt_pw = os.environ.get("DECRYPT_PASSWORD")
    if not decrypt_pw:
        print("[ERROR] DECRYPT_PASSWORD environment variable not set.")
        print("Please run with: DECRYPT_PASSWORD='your_password' python optimized_scheduler.py")
        sys.exit(1)
        
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
