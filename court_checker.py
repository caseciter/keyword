import os
import urllib.request
import json
from bs4 import BeautifulSoup

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

def fetch_fast_page_text(url):
    """Bypasses firewall and downloads page source instantly without browser overhead."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        html_content = response.read().decode('utf-8')
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text()

if __name__ == "__main__":
    keywords, match_all = get_keywords()
    print(f"Scanning {TARGET_URL} for: {keywords}")
    
    try:
        # Instant direct extraction
        page_text = fetch_fast_page_text(TARGET_URL).lower()
        print(f"[DEBUG] Document text layout scraped successfully ({len(page_text)} chars).")
        
        matches_found = [kw for kw in keywords if kw.lower() in page_text]
        is_found = len(matches_found) == len(keywords) if match_all else len(matches_found) > 0
        
        if is_found:
            print(f"[ALERT] Match discovered: {matches_found}")
            send_telegram_alert(matches_found)
        else:
            print("[INFO] No matching keywords found on current page layer.")
            
    except Exception as e:
        print(f"Extraction failed: {e}")
