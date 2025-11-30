import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Load env
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
PUBLIC_URL = os.getenv("PUBLIC_URL")

app = FastAPI()

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ------------------------------
#   Gemini – professional helper
# ------------------------------
async def ask_gemini(question: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": question}
                ]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=20)

        data = response.json()

        # Extract the text reply
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print("Gemini Error:", e)
        return "Sorry — unable to fetch an answer right now."


# ------------------------------
#  Telegram send message
# ------------------------------
async def send_message(chat_id, text):
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        })


# ------------------------------
#     Webhook setup
# ------------------------------
@app.get("/")
def home():
    return {"status": "Bot is running professionally with Gemini 💙"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    print("Telegram update:", update)

    if "message" not in update:
        return JSONResponse({"ok": True})

    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    # Greeting
    if text.lower() in ["/start", "hi", "hello", "hey"]:
        await send_message(
            chat_id,
            "Hello, Future CA!\n\n"
            "I’m your Study Assistant. How can I help you today?\n"
            "You can ask questions from:\n"
            "- Business Law\n"
            "- Mathematics, Statistics\n"
            "- Economics\n"
            "- Accounting (Basic theory)"
        )
        return {"ok": True}

    # Ask Gemini for any question
    reply = await ask_gemini(text)
    await send_message(chat_id, reply)
    return {"ok": True}


# ------------------------------
#     Set webhook (manual)
# ------------------------------
@app.get("/setwebhook")
async def set_webhook():
    if not PUBLIC_URL:
        return {"error": "PUBLIC_URL is missing"}

    url = f"{TELEGRAM_API}/setWebhook?url={PUBLIC_URL}/webhook"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.json()
