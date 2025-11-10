import os
import json
import sqlite3
import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# -------------------- بارگذاری تنظیمات --------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# -------------------- دیتابیس لیدها --------------------
conn = sqlite3.connect('leads.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS leads
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT,
                   message TEXT)''')
conn.commit()

# -------------------- فرمان استارت --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\nبه ربات برترگشت خوش اومدی!\nهر سوالی درباره تورها یا سفر داری بنویس تا کمکت کنم 🌍"
    )

# -------------------- پاسخ هوش مصنوعی --------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    username = update.message.from_user.username

    cursor.execute("INSERT INTO leads (username, message) VALUES (?, ?)", (username, user_message))
    conn.commit()

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        answer = response["choices"][0]["message"]["content"]
    except Exception as e:
        answer = "متأسفم، خطایی رخ داده 😔"

    await update.message.reply_text(answer)

# -------------------- اجرای ربات --------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
