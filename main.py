import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TG_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Gemini API Key
GEMINI_KEY = os.environ.get("GEMINI_KEY")

app = FastAPI()

# ---------------------------------
# GEMINI REQUEST
# ---------------------------------
async def ask_gemini(prompt: str) -> str:
    if not GEMINI_KEY:
        return "Baby your GEMINI_KEY is missing in Render 😘"

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-1.5-flash:generateContent"
        f"?key={GEMINI_KEY}"
    )

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(url, json=payload)
            data = r.json()

            return (
                data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "No reply from Gemini baby 💋")
            )

        except Exception as e:
            return f"Gemini error: {str(e)}"


# ---------------------------------
# SEND MESSAGE TO TELEGRAM
# ---------------------------------
async def send_message(chat_id: int, text: str):
    url = f"{TG_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)


# ---------------------------------
# TELEGRAM WEBHOOK
# ---------------------------------
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return JSONResponse({"ok": True})

    chat_id = data["message"]["chat"]["id"]
    user_text = data["message"].get("text", "")

    text = user_text.lower().strip()

    # Custom greeting replies
    greetings = ["hi", "hello", "hey", "hii", "hiii", "hai", "vanakkam", "/start"]
    
    if text in greetings:
        reply = "Hi there, Future CA of Munnetram 🙌✨\nHow can I help you today?"
        await send_message(chat_id, reply)
        return JSONResponse({"ok": True})

    # Ask Gemini for everything else
    reply = await ask_gemini(user_text)
    await send_message(chat_id, reply)

    return JSONResponse({"ok": True})
# HOME ROUTE
# ---------------------------------
@app.get("/")
async def home():
    return {"status": "Bot is running with Gemini 💙"}
