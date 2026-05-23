import os
import time
import urllib.request
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

TARGET_URL = "https://www.sci.gov.in/latest-orders/"

# --- EDIT YOUR DEFAULT AUTOMATED KEYWORDS HERE ---
# These are used for the automated hourly background scans
DEFAULT_KEYWORDS = ["Criminal", "Interim Order"]
DEFAULT_MATCH_ALL = False 
# ------------------------------------------------

def get_keywords():
    """Extracts keywords from GitHub manual actions input or falls back to defaults."""
    manual_keywords = os.environ.get("INPUT_KEYWORDS", "")
    manual_match_mode = os.environ.get("INPUT_MATCH_ALL", "")

    # If triggered manually with custom keywords
    if manual_keywords:
        print("[INFO] Using custom keywords provided via GitHub Actions panel.")
        keywords = [kw.strip() for kw in manual_keywords.split(",") if kw.strip()]
        match_all_mode = manual_match_mode.strip().lower() == "true"
        return keywords, match_all_mode

    # Otherwise, use the automated defaults defined above
    print("[INFO] Running automated check using default script keywords.")
    return DEFAULT_KEYWORDS, DEFAULT_MATCH_ALL

def send_telegram_alert(matched_words):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("[WARNING] Telegram credentials missing. Skipping notification.")
        return

    text_message = (
        f"🚨 *Supreme Court Alert*\n\n"
        f"Found keywords: {', '.join(matched_words)}\n"
        f"🔗 [View Latest Orders]({TARGET_URL})"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text_message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("Telegram notification sent successfully!")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def fetch_page_source(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)
        time.sleep(5) 
        return driver.page_source
    finally:
        driver.quit()

if __name__ == "__main__":
    keywords, match_all = get_keywords()
    print(f"Scanning {TARGET_URL} for: {keywords} (Match All: {match_all})")
    
    try:
        html = fetch_page_source(TARGET_URL)
        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text().lower()
        
        matches_found = [kw for kw in keywords if kw.lower() in page_text]
        is_found = len(matches_found) == len(keywords) if match_all else len(matches_found) > 0
        
        if is_found:
            print(f"[ALERT] Found matching text: {matches_found}")
            send_telegram_alert(matches_found)
        else:
            print("[INFO] No matching phrases found.")
            
    except Exception as e:
        print(f"Error during execution: {e}")
