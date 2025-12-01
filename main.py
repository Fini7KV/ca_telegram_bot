import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
from flask import Flask, request

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)
bot_app = None  # global reference for telegram app


# ----------------- AI RESPONSE -----------------
client = Groq(api_key=GROQ_API_KEY)

def ask_groq(question):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content


# ----------------- TELEGRAM HANDLERS -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am Nexus 🤖💙\nYour CA Foundation AI tutor.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    reply = ask_groq(user_text)
    await update.message.reply_text(reply)


# ----------------- FLASK WEBHOOK ROUTE -----------------
@app.route("/", methods=["GET"])
def home():
    return "Nexus bot is running!"

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    json_update = request.get_json()
    update = Update.de_json(json_update, bot_app.bot)
    bot_app.update_queue.put_nowait(update)
    return "OK"


# ----------------- MAIN INITIALIZER -----------------
async def init_telegram():
    global bot_app

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    bot_app = application

    # set webhook
    url = os.getenv("RENDER_EXTERNAL_URL") + f"/webhook/{TOKEN}"
    await application.bot.set_webhook(url=url)

    return application


def run():
    import asyncio
    asyncio.run(init_telegram())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


if __name__ == "__main__":
    run()
