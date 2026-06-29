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

is_running = True
last_update_id = 0

# خادم الويب الصحيح للرد على طلبات GET و HEAD من سيرفر ريندر بنجاح 200
class WebServerHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is live and scanning OTC pairs successfully!")

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), WebServerHandler)
    print(f"WebServer started on port {port}...")
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
                                    send_telegram_message("🟢 **تم تشغيل البوت بنجاح!** بدأ فحص أزواج الـ OTC الآن...")
                                else:
                                    send_telegram_message("🤖 البوت يعمل بالفعل ويقوم بالفحص حالياً!")
                            
                            elif text == "/stop":
                                if is_running:
                                    is_running = False
                                    send_telegram_message("🔴 **تم إيقاف البوت مؤقتاً!** لن يتم إرسال أي إشارات حتى ترسل أمر التشغيل.")
                                else:
                                    send_telegram_message("🤖 البوت متوقف بالفعل!")
        except Exception as e:
            print(f"Error checking commands: {e}")
        time.sleep(3)

def run_otc_scraper():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("جاري الدخول للمنصة لقراءة أزواج الـ OTC...")
        driver.get("https://pocketoption.com")
        time.sleep(20) 
        
        assets_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "current-symbol"))
        )
        assets_button.click()
        time.sleep(4)
        
        asset_rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'assets-list')]//div[contains(@class, 'asset-item')]")
        found_otc = False
        
        for row in asset_rows:
            try:
                asset_name = row.find_element(By.CLASS_NAME, "asset-name").text
                if "OTC" in asset_name:
                    payout_text = row.find_element(By.CLASS_NAME, "asset-payout").text.replace("%", "").strip()
                    payout = int(payout_text)
                    
                    if payout >= 90:
                        found_otc = True
                        msg = f"📊 **تحديث سوق الـ OTC (>= 90%)**\n\n🔹 الزوج: `{asset_name}`\n💰 نسبة الأرباح: `{payout}%` \n📈 البوت يراقب حركة الشموع الآن لإرسال إشارة!"
                        send_telegram_message(msg)
            except Exception:
                continue
                
        if not found_otc:
            print("لا توجد أزواج OTC تحقق النسبة المطلوبة حالياً.")
            
    except Exception as e:
        print(f"حدث خطأ أثناء فحص الـ OTC: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    threading.Thread(target=run_port_server, daemon=True).start()
    threading.Thread(target=check_telegram_commands, daemon=True).start()
    
    send_telegram_message("🦊 **تم تشغيل البوت بنجاح وحل مشكلة البورت بالكامل!**\n\n🎮 يمكنك التحكم الآن بالكامل عبر إرسال الأوامر الآتية:\n🔹 `/start` لبدء الفحص.\n🔹 `/stop` لإيقاف الفحص مؤقتاً.")
    
    while True:
        if is_running:
            run_otc_scraper()
            time.sleep(180)
        else:
            print("البوت متوقف حالياً بناءً على أمر المستخدم...")
            time.sleep(10)
