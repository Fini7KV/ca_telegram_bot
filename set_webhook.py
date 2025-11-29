import os, requests, sys
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PUBLIC_URL = os.environ.get("PUBLIC_URL")  # e.g. https://your-render-url.onrender.com
WEBHOOK_SECRET_PATH = os.environ.get("WEBHOOK_SECRET_PATH", "")
if not TELEGRAM_TOKEN or not PUBLIC_URL:
    print("Please set TELEGRAM_TOKEN and PUBLIC_URL env variables.")
    sys.exit(1)
hook = f"{PUBLIC_URL}/webhook{('/' + WEBHOOK_SECRET_PATH) if WEBHOOK_SECRET_PATH else ''}"
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
resp = requests.post(url, json={"url": hook, "max_connections": 40})
print(resp.status_code, resp.text)
