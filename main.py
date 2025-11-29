from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from pydantic import BaseModel
import os, httpx, json, asyncio, logging, math, time
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ca_telegram_bot")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
WEBHOOK_SECRET_PATH = os.environ.get("WEBHOOK_SECRET_PATH", "")  # optional extra security path segment

if not TELEGRAM_TOKEN or not OPENAI_KEY:
    logger.error("TELEGRAM_TOKEN and OPENAI_KEY environment variables are required.")
    # Do not exit - allow Render to show logs; raise on request if missing.

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

app = FastAPI(title="CA Telegram Bot (FastAPI webhook)")

# Load questions DB (simple JSON for sample; in production use Postgres/Mongo)
DB_PATH = "questions.json"
def load_db():
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not load questions.json, using empty DB: %s", e)
        return {"mtp": [], "rtp": [], "pyq": []}

# Telegram webhook update model (partial)
class MessageEntity(BaseModel):
    update_id: int
    message: Optional[Dict[str, Any]] = None
    edited_message: Optional[Dict[str, Any]] = None

async def call_openai(user_text: str) -> str:
    """
    Call OpenAI Chat Completions (v1) and return the assistant reply.
    Uses a lightweight request and conservative token usage.
    """
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a CA Foundation teaching assistant. Provide clear step-by-step answers, show workings for numeric problems, and mention relevant statutes/AS when applicable. Keep tone encouraging and concise."},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.0,
        "max_tokens": 800
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            j = r.json()
            return j["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error("OpenAI request failed: %s", e)
            return "Sorry — I couldn't fetch an answer right now. Please try again later."

async def telegram_send_message(chat_id: int, text: str, parse_mode: Optional[str] = None):
    """
    Send message to Telegram chat_id. Use httpx AsyncClient.
    """
    url = f"{TELEGRAM_API}/sendMessage"
    body = {"chat_id": chat_id, "text": text}
    if parse_mode:
        body["parse_mode"] = parse_mode
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            await client.post(url, json=body)
        except Exception as e:
            logger.error("Failed to send message: %s", e)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post(f"/webhook{('/' + WEBHOOK_SECRET_PATH) if WEBHOOK_SECRET_PATH else ''}")
async def webhook(update: MessageEntity, background_tasks: BackgroundTasks, request: Request):
    # Basic validation
    data = await request.json()
    msg = data.get("message") or data.get("edited_message")
    if not msg:
        return {"ok": True, "detail": "no message"}

    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text", "").strip() if msg.get("text") else ""

    if not text:
        # non-text messages ignored for now
        return {"ok": True, "detail": "no-text"}

    # Handle simple commands synchronously and heavy tasks in background
    lower = text.lower().strip()

    db = load_db()

    # Pre-defined commands
    if lower == "/start":
        await telegram_send_message(chat_id, "Hi! I'm your CA Foundation study bot. Commands:\n/mtp\n/rtp\n/pyq\n/test <n>\n/ask <question>")
        return {"ok": True}

    if lower == "/mtp":
        items = db.get("mtp", [])
        if not items:
            await telegram_send_message(chat_id, "No MTP items available yet.")
            return {"ok": True}
        pick = items[ (int(time.time()*1000) % len(items)) ]
        await telegram_send_message(chat_id, f"📘 MTP Question:\n\n{pick.get('question')}")
        return {"ok": True}

    if lower == "/rtp":
        items = db.get("rtp", [])
        if not items:
            await telegram_send_message(chat_id, "No RTP items available yet.")
            return {"ok": True}
        pick = items[ (int(time.time()*1000) % len(items)) ]
        await telegram_send_message(chat_id, f"📗 RTP Question:\n\n{pick.get('question')}")
        return {"ok": True}

    if lower == "/pyq":
        items = db.get("pyq", [])
        if not items:
            await telegram_send_message(chat_id, "No PYQ items available yet.")
            return {"ok": True}
        pick = items[ (int(time.time()*1000) % len(items)) ]
        await telegram_send_message(chat_id, f"📙 PYQ ({pick.get('year','NA')}):\n\n{pick.get('question')}")
        return {"ok": True}

    if lower.startswith("/test"):
        parts = lower.split()
        n = 5
        if len(parts) > 1:
            try:
                n = min(max(int(parts[1]), 1), 20)
            except:
                n = 5
        pool = db.get("mtp", []) + db.get("rtp", []) + db.get("pyq", [])
        if not pool:
            await telegram_send_message(chat_id, "No questions in DB to create a test.")
            return {"ok": True}
        # pick n items deterministically but pseudo-random
        out = f"📝 Quick Test — {n} questions:\n\n"
        idx = int(time.time()) % len(pool)
        for i in range(n):
            q = pool[(idx + i) % len(pool)]
            out += f"{i+1}. {q.get('question')}\n\n"
        await telegram_send_message(chat_id, out)
        return {"ok": True}

    if lower.startswith("/ask"):
        # send to OpenAI in background so webhook quickly returns
        user_q = text[4:].strip()
        if not user_q:
            await telegram_send_message(chat_id, "Please write your question after /ask")
            return {"ok": True}
        background_tasks.add_task(handle_ask_and_reply, chat_id, user_q)
        await telegram_send_message(chat_id, "Got it — preparing an answer. I'll send it shortly.")
        return {"ok": True}

    # fallback: treat text as question -> background OpenAI call
    background_tasks.add_task(handle_ask_and_reply, chat_id, text)
    await telegram_send_message(chat_id, "Thinking... I'll reply shortly.")
    return {"ok": True}

async def handle_ask_and_reply(chat_id: int, user_text: str):
    try:
        answer = await call_openai(user_text)
        # Truncate if extremely long
        if len(answer) > 4000:
            answer = answer[:3900] + "\n\n[Answer truncated]"
        await telegram_send_message(chat_id, answer)
    except Exception as e:
        logger.error("handle_ask_and_reply failed: %s", e)
        await telegram_send_message(chat_id, "Sorry, failed to fetch answer.")

