def send_telegram_alert(matched_words):
    """Sends a message alert directly to your Telegram App, cleaning hidden spacing bugs."""
    raw_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    raw_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not raw_token or not raw_chat_id:
        print("[WARNING] Telegram credentials missing. Skipping notification.")
        return

    # .strip() removes any accidental hidden spaces or new-line breaks (\n)
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
