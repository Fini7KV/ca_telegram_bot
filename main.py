import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from groq import Groq

# Load tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are NEXUS 🤖💙, a CA Foundation AI tutor.
You must always answer in exam-perfect, simple, structured language.

Subjects you teach:
• Law
• Accounts
• Economics
• Maths & Statistics

Examples of how you reply:
- "Explain Contract of Agency"
- "Solve depreciation: cost=100000, scrap=5000, life=5"
- "What is correlation?"

Your answers must be:
✓ Clear  
✓ Step-by-step  
✓ As per ICAI exam standard  
"""

async def ask_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama3-8b-8192",   # ✔ Correct Groq model
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response.choices[0].message["content"]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text

    # typing animation
    await update.message.chat.send_action(action="typing")

    reply = ask_groq(user_msg)
    reply = await reply  # await groq response

    await update.message.reply_text(f"{reply}\n\n— Nexus")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Nexus is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
