import os
import json
import sqlite3
import openai
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# -------------------------------
# بارگذاری تنظیمات
# -------------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY


# -------------------------------
# دیتابیس ذخیره لیدها
# -------------------------------
conn = sqlite3.connect("leads.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT
)
""")
conn.commit()


# -------------------------------
# تابع پاسخ هوش مصنوعی (نسل جدید OpenAI)
# -------------------------------
async def ai_answer(prompt):
    try:
        client = openai.OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message["content"]

    except Exception as e:
        return f"❌ خطا در ارتباط با هوش مصنوعی: {e}"


# -------------------------------
# دستور start
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سلام!\n"
        "من ربات *برترگشتBot* هستم.\n\n"
        "هر مقصدی خواستی بگو تا بهترین تورها + پاسخ هوش مصنوعی رو دریافت کنی 🌍✨",
        parse_mode="Markdown"
    )


# -------------------------------
# دریافت همه پیام‌ها
# -------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    text = update.message.text

    # ذخیره در دیتابیس
    cursor.execute("INSERT INTO leads (username, message) VALUES (?, ?)", (user, text))
    conn.commit()

    await update.message.reply_text("⏳ در حال بررسی درخواست...")

    # پاسخ هوش مصنوعی
    reply = await ai_answer(text)
    await update.message.reply_text(reply)


# -------------------------------
# اجرای ربات با ApplicationBuilder
# -------------------------------
def main():
    print("🚀 BartaGashtBot started successfully...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
