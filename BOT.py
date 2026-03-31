import time
import requests
import hashlib
from datetime import datetime
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 🔐 ENV VARIABLES (SET IN RAILWAY)
BOT_TOKEN = os.getenv("AAE0ZTgk4zMqe-w8vagA2PYB_VweWRiSNOA")
CHAT_ID = os.getenv("8686464812")

URL = "https://shop.royalchallengers.com/ticket"

last_hash = ""
last_hour_time = time.time()


def send_message(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": msg
        }
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)


print("🚀 BOT STARTED")

while True:
    driver = None
    try:
        # 🔥 HEADLESS MODE (NO WINDOW)
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        driver.get(URL)
        time.sleep(5)

        page = driver.page_source
        current_hash = hashlib.md5(page.encode()).hexdigest()

        print(f"{datetime.now()} → Checked")

        # 🚨 CHANGE DETECTION
        if last_hash != "" and current_hash != last_hash:
            send_message(f"🚨 WEBSITE CHANGED!\n⏰ {datetime.now()}")

        last_hash = current_hash

        # ⏰ HOURLY UPDATE
        if time.time() - last_hour_time >= 3600:
            send_message("✅ Checked for 1 hour — No change")
            last_hour_time = time.time()

    except Exception as e:
        print("Error:", e)

    finally:
        try:
            if driver:
                driver.quit()
        except:
            pass

    time.sleep(60)  # check every 1 minute