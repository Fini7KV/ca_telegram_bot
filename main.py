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
async def ask_gemini(prompt: str) -> str:
    if not GEMINI_KEY:
        return "API key error: Gemini key is missing on server."

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.post(url, json=payload)
            data = response.json()

            # Debug output to logs
            print("Gemini raw response:", data)

            # Extract Gemini output safely
            answer = (
                data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text")
            )

            if not answer:
                return "I’m sorry — unable to fetch an answer at the moment. Please try again."

            return answer.strip()

    except Exception as e:
        print("Gemini Error:", e)
        return "An error occurred while contacting Gemini."


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
