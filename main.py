import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
PUBLIC_URL = os.getenv("PUBLIC_URL")

app = FastAPI()

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ------------------------------------------------------
# ✔ WORKING GEMINI FUNCTION (gemini-1.5-flash)
# ------------------------------------------------------
import httpx

async def ask_gemini(question: str, gemini_key: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"

    payload = {
        "contents": [{
            "parts": [
                {"text": question}
            ]
        }]
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=payload)
            data = response.json()

            # Debug print
            print("Gemini Raw Response:", data)

            # Extract the text
            return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print("Gemini Error:", e)
        return "Sorry — unable to fetch an answer at the moment."

# ------------------------------------------------------
# ✔ Working send_message function
# ------------------------------------------------------
async def send_message(chat_id: int, text: str):
    url = f"{TELEGRAM_API}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)


# ------------------------------------------------------
# ✔ Home Route
# ------------------------------------------------------
@app.get("/")
def home():
    return {"status": "Bot is running with Gemini 💙"}


# ------------------------------------------------------
# ✔ TELEGRAM WEBHOOK
# ------------------------------------------------------
@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    print("Telegram update:", update)

    if "message" not in update:
        return {"ok": True}

    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    # Greetings
    if text.lower() in ["hi", "hello", "hey", "/start"]:
        greeting = (
            "Hello, Future CA of Munnetram ✨🙌\n\n"
            "I’m your Study Assistant. Ask me anything from:\n"
            "- Business Law 📘\n"
            "- Mathematics & Statistics 📊\n"
            "- Economics 💹\n"
            "- Accounting (Basic Theory) 📒\n\n"
            "How can I help you today?"
        )
        await send_message(chat_id, greeting)
        return {"ok": True}

    # Every other message → send to Gemini
    reply = await ask_gemini(text)
    await send_message(chat_id, reply)

    return {"ok": True}


# ------------------------------------------------------
# ✔ Manual webhook setup
# ------------------------------------------------------
@app.get("/setwebhook")
async def set_webhook():
    if not PUBLIC_URL:
        return {"error": "PUBLIC_URL is missing"}

    url = f"{TELEGRAM_API}/setWebhook?url={PUBLIC_URL}/webhook"

    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.json()
