import requests
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URLS = {
    "Третьяковская": "https://n1480962.yclients.com/company/1318073/activity/select",
    "Баррикадная": "https://n1480962.yclients.com/company/1318079/activity/select"
}
WAIT_SECONDS = 5
HEADLESS = True
DAYS_TO_CHECK = ["Friday", "Saturday", "Sunday"]

TELEGRAM_BOT_TOKEN = "**********"
TELEGRAM_CHAT_ID = "********"

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except:
        pass

def check_calendar_with_telegram(name, url):
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(WAIT_SECONDS)
    found_slots = []

    try:
        calendar_days = driver.find_elements(By.TAG_NAME, "ui-kit-calendar-day")
        today = datetime.today()
        current_month = today.month
        current_year = today.year

        for day in calendar_days:
            class_attr = day.get_attribute("class")
            try:
                day_number = day.find_element(By.CSS_SELECTOR, ".calendar-day-number-text").text.strip()
            except:
                continue
            if not day_number.isdigit():
                continue
            try:
                date_obj = datetime(current_year, current_month, int(day_number))
            except:
                continue
            weekday = date_obj.strftime("%A")
            if weekday not in DAYS_TO_CHECK:
                continue
            if "greyed-out" in class_attr:
                continue

            try:
                driver.execute_script("arguments[0].click();", day)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "activity-card-header"))
                )
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            except:
                continue

            activity_cards = driver.find_elements(By.CSS_SELECTOR, ".activity-card-header")
            for card in activity_cards:
                try:
                    time_label = card.find_element(By.CSS_SELECTOR, ".date-time").text.strip()
                except:
                    continue
                try:
                    availability = card.find_element(By.CSS_SELECTOR, ".availability-text")
                    text = availability.text.strip()
                    if "Нет мест" in text or "sold-out" in availability.get_attribute("class"):
                        continue
                    msg = f"✅ {name}: {time_label} — {text}" if text else f"✅ Свободно! {name}: {time_label}"
                    found_slots.append(msg)
                except:
                    msg = f"✅ {name}: {time_label}"
                    found_slots.append(msg)
    finally:
        driver.quit()

    if found_slots:
        send_telegram_message("\n".join(found_slots))

if __name__ == "__main__":
    while True:
        for name, url in URLS.items():
            check_calendar_with_telegram(name, url)
        time.sleep(300)
