# UniVerse

> [!WARNING]
> **Disclaimer:** This software is for educational and personal use only. The developer is not responsible for any misuse, account suspension, rate-limiting, or legal issues arising from the use of this tool. Use it at your own discretion and risk.
>
> This project is an independent developer tool and is not affiliated with, authorized, maintained, sponsored, or endorsed by the University of Patras (UPatras) or any of its affiliates.

## Feature Availability

| Feature |      General       |      UPatras       |        CEID        |
| :-----: | :----------------: | :----------------: | :----------------: |
| Eclass  | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Grades  |        :x:         | :white_check_mark: | :white_check_mark: |
|  News   |        :x:         |        :x:         | :white_check_mark: |

## Installation

```
pip install beautifulsoup4 playwright pycrypodome plyer asyncio aioconsole
playwright install
```

## Setup & Usage

### 1. Initial Account Registration
Run the main script once to register your credentials:
```bash
python main.py
```
This will prompt you for your login credentials and save them securely in an encrypted `data/user_credentials.json` file.

### 2. Discord Notification Setup (Optional)
If you want to receive instant notifications on Discord when a new grade is posted or updated:
1. Open Discord, go to your server settings or a specific channel's settings.
2. Go to **Integrations** > **Webhooks** > **Create Webhook**.
3. Copy the **Webhook URL**.
4. Paste it when prompted during the initial script setup, or add it manually to the `discord_webhook` field in `data/user_credentials.json`.

### 3. KDE Connect Phone Integration (Optional)
To automatically push grade files and course updates to your phone:
1. Make sure KDE Connect is installed and paired on both your PC and Android phone.
2. Run `kdeconnect-cli -l` in your terminal to list your paired devices and copy your Phone ID.
3. Paste the ID when prompted during initial setup, or add it manually to the `phone_id` field in `data/user_credentials.json`.

---

## Background Automation (Cron Scheduler)

To configure the script to check grades automatically in the background even if the main terminal is closed, you can schedule it as a system cron job:

1. Open your system's crontab config:
   ```bash
   crontab -e
   ```
2. Add a line to trigger the optimized background scheduler. Replace `/absolute/path/to/UniVerse` with the actual path to your repository, and `your_decryption_password` with the password you set during registration:
   ```bash
   0 * * * * cd /absolute/path/to/UniVerse && DECRYPT_PASSWORD="your_decryption_password" /absolute/path/to/UniVerse/.venv/bin/python optimized_scheduler.py >> /absolute/path/to/UniVerse/cron.log 2>&1
   ```

> [!CAUTION]
> **CRITICAL RATE LIMIT WARNINGS (BUILT-IN SAFETY):**
> Frequent automated logins will trigger UPatras portal defenses, potentially leading to automated **IP bans/blocks** or **account suspension**. To protect your account, the codebase has built-in safety checks:
> 
> 1. **Interactive Scheduler (main.py):** The menu scheduler explicitly rejects any interval under **60 minutes**.
> 2. **Manual Check (Option 2):** If you attempt to check grades manually less than **30 minutes** after your last run, the app will warn you and require confirmation before proceeding.
> 3. **Background Scheduler (optimized_scheduler.py):**
>    - Enforces a default safety cooldown of **60 minutes**. Any run triggered within the cooldown period is silently skipped.
>    - You can pass an optional custom interval argument (in minutes, e.g., `python optimized_scheduler.py 90`), but the script will throw an error and exit if you specify any value **under 60 minutes** (e.g., `python optimized_scheduler.py 30`).

---

## Todo:
- Make eclass async like progress
- Implement aioconsole for async input to avoid scheduler hangs
