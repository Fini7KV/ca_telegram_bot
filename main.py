import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

APP_URL = "https://ca-telegram-bot-1.onrender.com"

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = APP_URL + WEBHOOK_PATH
PORT = int(os.environ.get("PORT", 10000))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am Nexus 🤖💙 Your CA Foundation AI tutor.")


async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are Nexus, a CA Foundation tutor."},
            {"role": "user", "content": text},
        ],
        model="llama3-8b-8192",
    )

    answer = completion.choices[0].message["content"]
    await update.message.reply_text(answer)


async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))

    # START WEBHOOK SERVER (NO app.start() – THIS IS CORRECT FOR RENDER)
    await app.initialize()
    await app.bot.set_webhook(WEBHOOK_URL)

    await app.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_URL,
    )

    print("🚀 Nexus is running with webhook on Render!")
    await app.idle()


if __name__ == "__main__":
    asyncio.run(main())
