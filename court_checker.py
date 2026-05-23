import os
import time
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

TARGET_URL = "https://www.sci.gov.in/latest-orders/"

# --- EDIT YOUR KEYWORDS HERE ---
KEYWORDS_TO_FIND = ["Criminal", "Interim Order"] 
MATCH_ALL = False 
# ------------------------------

def send_email_alert(matched_words):
    """Sends an email notification using GitHub Secrets."""
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")
    
    if not all([sender, password, receiver]):
        print("[WARNING] Email credentials missing. Skipping email alert.")
        return

    msg = MIMEText(f"The automated checker found a match for your keywords: {matched_words}\n\nCheck the page here: {TARGET_URL}")
    msg['Subject'] = f" Supreme Court Alert: Keywords Found!"
    msg['From'] = sender
    msg['To'] = receiver

    try:
        # Using Gmail's SMTP server as a standard example
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, [receiver], msg.as_string())
        print("Alert email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

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
    print(f"Scanning {TARGET_URL}...")
    try:
        html = fetch_page_source(TARGET_URL)
        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text().lower()
        
        matches_found = [kw for kw in KEYWORDS_TO_FIND if kw.lower() in page_text]
        is_found = len(matches_found) == len(KEYWORDS_TO_FIND) if MATCH_ALL else len(matches_found) > 0
        
        if is_found:
            print(f"[ALERT] Found keywords: {matches_found}")
            send_email_alert(matches_found)
        else:
            print("[INFO] No matching keywords found.")
            
    except Exception as e:
        print(f"Error: {e}")
