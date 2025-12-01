# main.py
import os
import time
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# optional: import and use the groq client if you prefer
try:
    from groq import Groq
    HAS_GROQ = True
except Exception:
    HAS_GROQ = False

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN not set in environment")

# Render provides a public URL in RENDER_EXTERNAL_URL (or set your own)
APP_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("APP_URL")
if not APP_URL:
    print("Warning: RENDER_EXTERNAL_URL / APP_URL not set. Webhook setup will fail until deployed.")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = (APP_URL + WEBHOOK_PATH) if APP_URL else None

PORT = int(os.getenv("PORT", 10000))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY and HAS_GROQ:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    groq_client = None

app = Flask(__name__)

def set_telegram_webhook():
    if not WEBHOOK_URL:
        print("No WEBHOOK_URL (APP_URL missing). Skipping setWebhook.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    payload = {"url": WEBHOOK_URL}
    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        j = r.json()
        print("setWebhook response:", j)
        return j.get("ok", False)
    except Exception as e:
        print("Failed to set webhook:", e)
        return False

def ask_groq(question: str) -> str:
    if groq_client:
        try:
            resp = groq_client.chat.completions.create(
                model="llama3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are Nexus, an exam-focused CA Foundation tutor. Keep answers simple, clear, and exam-oriented."},
                    {"role": "user", "content": question}
                ],
                max_tokens=3000,
            )
            return resp.choices[0].message["content"].strip()
        except Exception as e:
            print("Groq error:", e)
            return "Sorry Aspirant, Groq had an issue. Try again."
    else:
        return "Groq not configured. Set GROQ_API_KEY."
        # fallback / testing reply
        return "Groq not configured. Set GROQ_API_KEY in environment to enable AI replies."

@app.route("/", methods=["GET"])
def home():
    return "Nexus (Telegram webhook) is alive", 200

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"status": "no json"}), 400

    # Only handle messages; ignore other update types for now
    msg = data.get("message") or data.get("edited_message")
    if not msg:
        return "", 200

    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text", "").strip() if msg.get("text") else ""

    if not chat_id or not text:
        return "", 200

    # quick command handler
    if text.startswith("/start"):
        reply_text = "Hello! I am Nexus 🤖💙 Your CA Foundation AI tutor.\nAsk me anything: Law, Accounts, Maths & Stats, Economics."
    else:
        # call Groq or fallback
        reply_text = ask_groq(text)

    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": reply_text}
    try:
        r = requests.post(send_url, json=payload, timeout=15)
        # don't raise to avoid failing webhook; just log
        print("sendMessage status:", r.status_code, r.text[:500])
    except Exception as e:
        print("Failed to sendMessage:", e)

    return "", 200

if __name__ == "__main__":
    # Give Render a second to set envs reliably
    time.sleep(0.5)

    # Try set webhook if we have APP_URL
    if WEBHOOK_URL:
        ok = set_telegram_webhook()
        if not ok:
            print("Warning: setWebhook returned false. Check APP_URL and BOT_TOKEN.")

    # Start Flask (Render will run this)
    print(f"Starting Flask on 0.0.0.0:{PORT}, webhook path {WEBHOOK_PATH}")
    app.run(host="0.0.0.0", port=PORT)
