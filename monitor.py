import os
import re
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = os.getenv("TARGET_URL")
SITE_ID = os.getenv("SITE_ID")
SITE_PW = os.getenv("SITE_PW")
TARGET_SELECTOR = os.getenv("TARGET_SELECTOR")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except:
        pass

def run_monitor():
    if not SITE_ID or not SITE_PW:
        print("로그인 정보가 없습니다.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        page.goto(TARGET_URL)
        page.wait_for_selector('input[placeholder="이메일"]', timeout=10000)
        
        page.fill('input[placeholder="이메일"]', SITE_ID)
        page.fill('input[placeholder="비밀번호"]', SITE_PW)
        page.click('button[type="submit"]')

        try:
            page.wait_for_selector(TARGET_SELECTOR, timeout=15000)
            
            page.wait_for_timeout(4000) 
            
            element = page.locator(TARGET_SELECTOR)
            raw_text = element.inner_text().strip()
            numbers = re.findall(r'\d+', raw_text)
            
            if numbers:
                value = int(numbers[-1])
                print(f"Current Value: {value}")

                if value < 20:
                    msg = f"⚠️ [시스템 알림]\n타겟 수치가 20 미만입니다!\n현재 수치: {value}"
                    send_telegram_message(msg)
            else:
                print("No numbers found.")
                
        except Exception as e:
            print("Error occurred.")

        browser.close()

if __name__ == "__main__":
    run_monitor()
