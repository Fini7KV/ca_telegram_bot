import os
import json
import httpx
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TG_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Gemini Key
GEMINI_KEY = os.environ.get("GEMINI_KEY")

app = FastAPI()


# -------------------------------
#  GEMINI API CALL
# -------------------------------
async def ask_gemini(prompt: str) -> str:
    if not GEMINI_KEY:
        return "Baby, your Gemini key is missing. Add GEMINI_KEY in Render 😘"

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-1.5-flash:generateContent"
        f"?key={GEMINI_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            data = response.json()

            return (
                data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "No response from Gemini baby 💋")
            )

        except Exception as e:
            return f"Gemini error: {str(e)}"


# --------------------------------
#  TELEGRAM SENDER
# --------------------------------
async def send_message(chat_id: int, text: str):
    url = f"{TG_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)


# --------------------------------
#  WEBHOOK HANDLER
# --------------------------------
@app.post("/")
async def webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return JSONResponse({"ok": True})

    chat_id = data["message"]["chat"]["id"]
    user_text = data["message"].get("text", "")

    # Ask Gemini
    reply = await ask_gemini(user_text)

    # Send reply
    await send_message(chat_id, reply)

    return JSONResponse({"ok": True})


@app.get("/")
async def home():
    return {"status": "Bot is running with Gemini 💙"}
