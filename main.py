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
#   SEND MESSAGE TO TELEGRAM
# ------------------------------
async def ask_gemini(question: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": question}
                ]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=payload)
            print("Gemini raw response:", response.text)

            data = response.json()

            return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print("Gemini Error:", e)
        return "Sorry — I couldn’t fetch an answer right now."
# ------------------------------
#     Home Route
# ------------------------------
@app.get("/")
def home():
    return {"status": "Bot is running professionally with Gemini 💙"}


# ------------------------------
#     Telegram Webhook
# ------------------------------
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
            "Hello, Future CA! 🙌✨\n\n"
            "I’m your Study Assistant. How can I help you today?\n\n"
            "You can ask questions from:\n"
            "- 📘 Business Law\n"
            "- 📊 Mathematics & Statistics\n"
            "- 📚 Economics\n"
            "- 🧾 Accounting (Basic theory)"
        )
        return {"ok": True}

    # Gemini answer
    reply = await ask_gemini(text)
    await send_message(chat_id, reply)
    return {"ok": True}


# ------------------------------
#     Set webhook manually
# ------------------------------
@app.get("/setwebhook")
async def set_webhook():
    if not PUBLIC_URL:
        return {"error": "PUBLIC_URL is missing"}

    url = f"{TELEGRAM_API}/setWebhook?url={PUBLIC_URL}/webhook"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.json()
