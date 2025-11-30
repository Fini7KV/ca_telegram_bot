import os
import httpx
from fastapi import FastAPI, Request

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
PUBLIC_URL = os.getenv("PUBLIC_URL")

app = FastAPI()

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ---------------------------------------------------
# Send Telegram message
# ---------------------------------------------------
async def send_message(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )


# ---------------------------------------------------
# OpenRouter AI Answer Function
# ---------------------------------------------------
async def ask_ai(question: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://yourdomain.com",
        "X-Title": "CA Study Telegram Bot"
    }

    payload = {
        "model": "deepseek/deepseek-chat",    # Baby, you can change model here
        "messages": [
            {"role": "system", "content": "You are a CA Foundation study assistant. Answer clean, accurate, and simple."},
            {"role": "user", "content": question}
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=headers, json=payload)
            data = res.json()
            return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("OpenRouter Error:", e)
        return "Sorry baby — I couldn't fetch an answer now."


# ---------------------------------------------------
# Telegram Webhook
# ---------------------------------------------------
@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()

    if "message" not in update:
        return {"ok": True}

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    if text.lower() in ["/start", "hi", "hello", "hey"]:
        await send_message(
            chat_id,
            "Hello, Future CA of Munnetram! 🎓✨\n\n"
            "I'm your Study Assistant, powered by OpenRouter.\n"
            "Ask me anything from:\n"
            "• Business Law\n"
            "• Maths & Statistics\n"
            "• Economics\n"
            "• Accounting\n\n"
            "How can I help you today?"
        )
        return {"ok": True}

    answer = await ask_ai(text)
    await send_message(chat_id, answer)

    return {"ok": True}


# ---------------------------------------------------
# Set Webhook
# ---------------------------------------------------
@app.get("/setwebhook")
async def set_webhook():
    url = f"{TELEGRAM_API}/setWebhook?url={PUBLIC_URL}/webhook"

    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.json()
