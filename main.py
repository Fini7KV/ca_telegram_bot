# main.py
import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Load ENV
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
BOT_NAME = "Nexus"

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise Exception("Missing TELEGRAM_TOKEN or GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Nexus, an intelligent CA Foundation tutor. "
    "When answering: give definition, key points, formulas/sections, examples, and exam tips. "
    "For numerical problems: show step-by-step calculations. "
    "Keep answers clear and helpful. End every answer with '— Nexus'."
)

# ------------------ Groq Query ------------------
def groq_query(prompt: str) -> str:
    url = f"{GROQ_BASE_URL}/responses"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3b",
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_output_tokens": 800,
        "temperature": 0.1
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    # extract text
    if "output_text" in data:
        return data["output_text"]

    if "output" in data and isinstance(data["output"], list):
        first = data["output"][0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return first.get("content") or first.get("text") or str(first)

    return str(data)


# ----------------- Telegram Handlers -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Hello! I am Nexus 🤖💙\n"
        "Your CA Foundation AI tutor.\n\n"
        "Ask me anything:\n"
        "• Law\n"
        "• Accounts\n"
        "• Maths & Stats\n"
        "• Economics\n\n"
        "Examples:\n"
        "• Explain Contract of Agency\n"
        "• Solve depreciation: cost=100000, scrap=5000, life=5\n"
        "• What is correlation?\n\n"
        "I will always answer in an exam-perfect format.\n"
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ask any CA Foundation question.\n"
        "Examples:\n"
        "- Explain partnership deed\n"
        "- Solve linear regression\n"
        "- Journal entry for bad debts\n\n"
        "I will answer with steps, examples, and exam tips.\n"
        "— Nexus"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # Problem-solving detection
    if "solve" in user_text.lower() or any(char.isdigit() for char in user_text):
        prompt = "Solve step-by-step: " + user_text
    else:
        prompt = user_text

    try:
        await update.message.reply_chat_action("typing")
        answer = groq_query(prompt)
    except Exception as e:
        await update.message.reply_text("Error contacting Groq. Try again.")
        return

    if not answer.endswith("— Nexus"):
        answer += "\n\n— Nexus"

    await update.message.reply_text(answer, parse_mode=ParseMode.HTML)


# ------------------- Run Bot -------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )

    print("Nexus AI Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
