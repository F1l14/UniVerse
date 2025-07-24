# UniVerse

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

## Instructions

Register on the app once to let the data/user_credentials.json file to be created. Then use `kdeconnect-cli -l` to get your phone's id and paste it on the user_credentials.json on the `phone_id`.
todo:

```
make eclass async like progress
implement aioconsole for async input to avoid scheduler hangs
```
