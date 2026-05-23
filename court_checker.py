import os
import time
import urllib.request
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

TARGET_URL = "https://www.sci.gov.in/latest-orders/"

# --- EDIT YOUR DEFAULT AUTOMATED KEYWORDS HERE ---
DEFAULT_KEYWORDS = ["Criminal", "Interim Order"]
DEFAULT_MATCH_ALL = False 
# ------------------------------------------------

def get_keywords():
    """Extracts keywords from GitHub manual actions input or falls back to defaults."""
    manual_keywords = os.environ.get("INPUT_KEYWORDS", "")
    manual_match_mode = os.environ.get("INPUT_MATCH_ALL", "")

    if manual_keywords:
        print("[INFO] Using custom keywords provided via GitHub Actions panel.")
        keywords = [kw.strip() for kw in manual_keywords.split(",") if kw.strip()]
        match_all_mode = manual_match_mode.strip().lower() == "true"
        return keywords, match_all_mode

    print("[INFO] Running automated check using default script keywords.")
    return DEFAULT_KEYWORDS, DEFAULT_MATCH_ALL

def send_telegram_alert(matched_words):
    """Sends a message alert directly to your Telegram App."""
    raw_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    raw_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not raw_token or not raw_chat_id:
        print("[WARNING] Telegram credentials missing. Skipping notification.")
        return

    bot_token = raw_token.strip()
    chat_id = raw_chat_id.strip()

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

def fetch_page_source_and_extract_text(url):
    """Launches Selenium, waits for the table/body to load, and extracts deep text."""
    options = Options()
    options.add_argument("--headless=new") # Modern headless flag
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)
        
        # Explicitly wait up to 15 seconds for the body text layout to fully activate
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5) # Final safety buffer for background AJAX frames to fill
        
        # Extract direct visible text from the browser engine rather than raw unrendered HTML string
        visible_text = driver.find_element(By.TAG_NAME, "body").text
        return visible_text
    finally:
        driver.quit()

if __name__ == "__main__":
    keywords, match_all = get_keywords()
    print(f"Scanning {TARGET_URL} for: {keywords} (Match All: {match_all})")
    
    try:
        # Fetch rendered textual data directly from browser memory
        page_text = fetch_page_source_and_extract_text(TARGET_URL).lower()
        
        # Diagnostics: Print a small snippet of extracted data to GitHub console logs
        print(f"[DEBUG] Raw extracted text length: {len(page_text)} characters.")
        
        matches_found = [kw for kw in keywords if kw.lower() in page_text]
        is_found = len(matches_found) == len(keywords) if match_all else len(matches_found) > 0
        
        if is_found:
            print(f"[ALERT] Match discovered: {matches_found}")
            send_telegram_alert(matches_found)
        else:
            print("[INFO] No matching keywords discovered on the current page view window.")
            
    except Exception as e:
        print(f"Runtime execution failure error: {e}")
