import os
import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# بيانات تليجرام الخاصة بك
BOT_TOKEN = "7963335503:AAHwscvP-R9Z6-UaU40U-Uf8fX98XfX98Xf"  
CHAT_ID = "941436059"

# بيانات حسابك الصحيحة والجديدة في منصة Pocket Option
POCKET_EMAIL = "unknown.sex.unknown@gmail.com"
POCKET_PASSWORD = "yCKuZH2u"

is_running = True
last_update_id = 0

class WebServerHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
        
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is live and scanning OTC pairs successfully!")

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), WebServerHandler)
    server.serve_forever()

def send_telegram_message(message):
    url = f"https://telegram.org{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def check_telegram_commands():
    global is_running, last_update_id
    url = f"https://telegram.org{BOT_TOKEN}/getUpdates"
    while True:
        try:
            params = {"offset": last_update_id + 1, "timeout": 10}
            response = requests.get(url, params=params, timeout=15).json()
            if "result" in response:
                for update in response["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update and "text" in update["message"]:
                        text = update["message"]["text"].strip().lower()
                        user_chat_id = str(update["message"]["chat"]["id"])
                        if user_chat_id == CHAT_ID:
                            if text == "/start":
                                if not is_running:
                                    is_running = True
                                    send_telegram_message("🟢 **تم إعادة تشغيل فحص أزواج الـ OTC بنجاح!**")
                            elif text == "/stop":
                                if is_running:
                                    is_running = False
                                    send_telegram_message("🔴 **تم إيقاف البوت مؤقتاً!**")
        except Exception:
            pass
        time.sleep(3)

def run_otc_scraper():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.binary_location = "/usr/bin/chromium"
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://pocketoption.com")
        time.sleep(15)
        
        assets_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "current-symbol"))
        )
        assets_button.click()
        time.sleep(3)
        
        asset_rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'assets-list')]//div[contains(@class, 'asset-item')]")
        
        otc_pairs_list = []
        
        for row in asset_rows:
            try:
                asset_name = row.find_element(By.CLASS_NAME, "asset-name").text
                if "OTC" in asset_name:
                    payout_text = row.find_element(By.CLASS_NAME, "asset-payout").text.replace("%", "").strip()
                    payout_val = int(payout_text)
                    
                    if payout_val >= 90:
                        otc_pairs_list.append(f"🔹 `{asset_name}` ➡️ نسبة الأرباح: *{payout_val}%*")
            except Exception:
                continue
        
        if otc_pairs_list:
            message_header = "📊 **تقرير أزواج الـ OTC المتاحة (>= 90%):**\n\n"
            full_message = message_header + "\n".join(otc_pairs_list) + "\n\n📈 البوت يراقب حركة السوق الآن!"
            send_telegram_message(full_message)
        else:
            print("لم يتم العثور على أزواج OTC تحقق النسبة المطلوبة حالياً.")
            
        driver.quit()
    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_port_server, daemon=True).start()
    threading.Thread(target=check_telegram_commands, daemon=True).start()
    
    send_telegram_message("Fox **تم تشغيل البوت بنجاح وحل مشكلة البورت والمتصفح!**\n\nتم تسجيل الباسورد الجديد وجاري سحب أسماء أزواج الـ OTC الحية وإرسالها لك...\n\n🎮 الأوامر المتاحة:\n🔹 `/start` لبدء الفحص\n🔹 `/stop` للإيقاف")
    
    while True:
        if is_running:
            run_otc_scraper()
            time.sleep(180)
        else:
            time.sleep(10)
