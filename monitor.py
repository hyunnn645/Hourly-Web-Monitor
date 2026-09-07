import os
import re
import requests
import subprocess
from playwright.sync_api import sync_playwright

TARGET_URL = os.getenv("TARGET_URL")
SITE_ID = os.getenv("SITE_ID")
SITE_PW = os.getenv("SITE_PW")
AUTH_COOKIE = os.getenv("AUTH_COOKIE")
TARGET_SELECTOR = os.getenv("TARGET_SELECTOR2")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GH_PAT = os.getenv("GH_PAT")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")

def update_github_secret(new_cookie):
    """봇이 획득한 새 쿠키를 GitHub Secrets에 스스로 저장합니다."""
    if not GH_PAT or not GITHUB_REPOSITORY:
        print("GH_PAT가 없어 Secret 자동 갱신을 건너뜁니다.")
        return
    try:
        env = os.environ.copy()
        env["GH_TOKEN"] = GH_PAT
        subprocess.run(['gh', 'secret', 'set', 'AUTH_COOKIE', '-b', new_cookie, '-R', GITHUB_REPOSITORY], check=True, env=env)
        print("✅ 쿠키 만료 감지됨: 새 쿠키를 발급받아 자동 덮어썼습니다.")
    except Exception as e:
        print(f"Secret 업데이트 실패: {e}")

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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        if AUTH_COOKIE:
            domain = ".miricanvas.com"
            cookies = []
            for pair in AUTH_COOKIE.split(";"):
                if "=" in pair:
                    name, value = pair.strip().split("=", 1)
                    cookies.append({"name": name, "value": value, "domain": domain, "path": "/"})
            context.add_cookies(cookies)

        page = context.new_page()
        page.goto(TARGET_URL)

        try:
            page.wait_for_selector('input[placeholder="이메일"]', timeout=5000)
            is_login_required = True
        except:
            is_login_required = False

        if is_login_required:
            print("로그인이 필요합니다. 비상 로그인을 시도합니다.")
            if not SITE_ID or not SITE_PW:
                print("로그인 정보가 없습니다.")
                return
            
            page.fill('input[placeholder="이메일"]', SITE_ID)
            page.fill('input[placeholder="비밀번호"]', SITE_PW)
            
            try:
                page.locator('label:has-text("로그인 유지하기")').click(timeout=3000)
            except:
                pass
                
            page.click('button[type="submit"]')
            page.wait_for_timeout(5000)
            
            new_cookies = context.cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in new_cookies])
            update_github_secret(cookie_str)
            
            page.goto(TARGET_URL)

        try:
            page.wait_for_selector(TARGET_SELECTOR, timeout=15000)
            element = page.locator(TARGET_SELECTOR)
            
            element.element_handle().wait_for_function('el => el.innerText.trim() !== ""', timeout=5000)

            raw_text = element.inner_text().strip()
            numbers = re.findall(r'\d+', raw_text)
            
            if numbers:
                value = int(numbers[-1])
                print(f"Current Value: {value}")

                if value < 20:
                    msg = f"⚠️ [알림]\n가능 수치: {20-value}"
                    send_telegram_message(msg)
            else:
                print("No numbers found.")
                
        except Exception as e:
            print(f"Error occurred: {e}")

        browser.close()

if __name__ == "__main__":
    run_monitor()
