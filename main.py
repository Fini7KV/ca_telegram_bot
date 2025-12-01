import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from groq import Groq

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are NEXUS 🤖💙, a CA Foundation AI tutor.
Always answer with exam-perfect clarity.
Subjects: Law, Accounts, Maths & Stats, Economics.
"""

async def ask_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama3-8b-8192",  # ✔ Works perfectly on Groq
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response.choices[0].message["content"]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.chat.send_action("typing")

    answer = await ask_groq(text)
    await update.message.reply_text(f"{answer}\n\n— Nexus")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Nexus is running…")
    app.run_polling()  # ✔ No async wrapper, no event loop crash

if __name__ == "__main__":
    main()
