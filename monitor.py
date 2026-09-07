import os
import re
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = os.getenv("TARGET_URL")
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

def check_account(browser, account_name, site_id, site_pw):
    if not site_id or not site_pw:
        print(f"{account_name}: 로그인 정보가 없습니다.")
        return

    # 💡 브라우저는 공유하되, 정보가 섞이지 않도록 완벽히 독립된 시크릿 탭(Context) 생성
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    page = context.new_page()

    # 🚀 핵심 최적화: 이미지, 미디어, 폰트 다운로드를 차단하여 로딩 속도 극대화
    page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

    try:
        page.goto(TARGET_URL)
        page.wait_for_selector('input[placeholder="이메일"]', timeout=10000)
        
        page.fill('input[placeholder="이메일"]', site_id)
        page.fill('input[placeholder="비밀번호"]', site_pw)
        page.click('button[type="submit"]')

        page.wait_for_selector(TARGET_SELECTOR, timeout=15000)
        
        # 🚀 대기 시간 최적화: 4초 대기를 1.5초로 축소
        page.wait_for_timeout(1500)

        raw_text = page.locator(TARGET_SELECTOR).inner_text().strip()
        numbers = re.findall(r'\d+', raw_text)
        
        if numbers:
            value = int(numbers[-1])
            print(f"{account_name} Current Value: {value}")

            if value < 20:
                msg = f"⚠️ [알림]\n{account_name} 가능 수치: {20-value}"
                send_telegram_message(msg)
        else:
            print(f"{account_name}: No numbers found.")
            
    except Exception as e:
        print(f"{account_name} Error occurred: {e}")
    finally:
        # 검사가 끝난 계정의 시크릿 탭만 깔끔하게 닫아줍니다.
        context.close()

def run_monitor():
    accounts = [
        {"name": "계정 1", "id": os.getenv("SITE_ID_1"), "pw": os.getenv("SITE_PW_1")},
        {"name": "계정 2", "id": os.getenv("SITE_ID_2"), "pw": os.getenv("SITE_PW_2")}
    ]

    with sync_playwright() as p:
        # 🚀 핵심 최적화: 무거운 크롬 브라우저 실행은 전체 과정에서 딱 한 번만 수행
        browser = p.chromium.launch(headless=True)
        
        for acc in accounts:
            print(f"--- {acc['name']} 확인 시작 ---")
            # 켜둔 브라우저(browser)를 통째로 넘겨서 재사용합니다.
            check_account(browser, acc["name"], acc["id"], acc["pw"])
        
        # 모든 계정 검사가 끝나면 최종적으로 브라우저 종료
        browser.close()

if __name__ == "__main__":
    run_monitor()
