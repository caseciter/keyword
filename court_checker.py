import os
import urllib.request
import json
from bs4 import BeautifulSoup

TARGET_URL = "https://www.sci.gov.in/latest-orders/"

def get_telegram_updates(bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("result", [])
    except Exception as e:
        print(f"[ERROR] Failed to fetch Telegram updates: {e}")
        return []

def update_github_variable(token, repo, var_name, value_string):
    url = f"https://api.github.com/repos/{repo}/actions/variables/{var_name}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    payload = {"name": var_name, "value": value_string}
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="PATCH")
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 204]:
                print(f"[SUCCESS] Synced keywords to GitHub: {value_string}")
    except Exception as e:
        print(f"[ERROR] Failed to update GitHub Variable: {e}")

def send_telegram_msg(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Telegram reply error: {e}")

def fetch_deep_page_text(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        soup = BeautifulSoup(response.read().decode('utf-8', errors='ignore'), 'html.parser')
        text_pieces = [el.get_text(strip=True) for el in soup.find_all(['td', 'th', 'a', 'span', 'p'])]
        return " ".join(text_pieces).lower()

if __name__ == "__main__":
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    gh_pat = os.environ.get("GH_PAT", "").strip()
    repo_name = os.environ.get("GITHUB_REPOSITORY", "").strip()

    raw_keywords = os.environ.get("STORED_KEYWORDS", "")
    current_keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]

    updates = get_telegram_updates(bot_token)
    changed = False

    for update in updates:
        msg = update.get("message", {})
        text = msg.get("text", "").strip()
        from_id = str(msg.get("chat", {}).get("id", ""))

        if from_id != chat_id:
            continue 

        if text.startswith("/add "):
            new_kw = text.replace("/add ", "").strip()
            if new_kw and new_kw not in current_keywords:
                current_keywords.append(new_kw)
                changed = True
                send_telegram_msg(bot_token, chat_id, f"➕ Added keyword: `{new_kw}`")
        
        elif text.startswith("/remove "):
            rem_kw = text.replace("/remove ", "").strip()
            if rem_kw in current_keywords:
                current_keywords.remove(rem_kw)
                changed = True
                send_telegram_msg(bot_token, chat_id, f"➖ Removed keyword: `{rem_kw}`")
        
        elif text == "/removeall":
            current_keywords = []
            changed = True
            send_telegram_msg(bot_token, chat_id, "🗑️ *Watchlist Cleared!* All keywords have been removed.")
        
        elif text == "/list":
            if current_keywords:
                send_telegram_msg(bot_token, chat_id, f"📋 *Active Watchlist:*\n" + "\n".join([f"• {k}" for k in current_keywords]))
            else:
                send_telegram_msg(bot_token, chat_id, "📋 Watchlist is currently empty.")

    if changed and gh_pat and repo_name:
        updated_string = ", ".join(current_keywords)
        update_github_variable(gh_pat, repo_name, "STORED_KEYWORDS", updated_string)

    # Scrape only if we have keywords to track
    if current_keywords:
        print(f"Scanning Court site for active watchlist: {current_keywords}")
        try:
            page_content = fetch_deep_page_text(TARGET_URL)
            matches = [kw for kw in current_keywords if kw.lower() in page_content]

            if matches:
                send_telegram_msg(bot_token, chat_id, f"🚨 *Court Match Discovered!*\n\nFound terms: {', '.join(matches)}\n🔗 [View Orders]({TARGET_URL})")
        except Exception as e:
            print(f"Scraper error: {e}")
    else:
        print("[INFO] Watchlist empty. Skipping page download layer.")
