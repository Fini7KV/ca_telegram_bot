import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEBHOOK_URL = f"https://ca-telegram-bot-1.onrender.com/webhook/{BOT_TOKEN}"

client = Groq(api_key=GROQ_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am Nexus 🤖💙 Your CA Foundation AI tutor.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are Nexus, a CA Foundation AI tutor."},
            {"role": "user", "content": user_msg},
        ],
        model="llama3-8b-8192",
    )

    reply = chat_completion.choices[0].message["content"]
    await update.message.reply_text(reply)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start webhook server
    await app.start()
    await app.bot.set_webhook(WEBHOOK_URL)

    print("Nexus is running with webhook…")

    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL
    )

    await app.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
