import os
import json
import sqlite3
import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

# بارگذاری متغیرها از Environment یا فایل .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# اتصال به دیتابیس برای ذخیره لیدها
conn = sqlite3.connect('leads.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT
)''')
conn.commit()

# بارگذاری داده‌ی تورها از فایل JSON
try:
    with open("tours.json", "r", encoding="utf-8") as f:
        tours = json.load(f)
except Exception:
    tours = []

# ----------------- دستورات ربات -----------------

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(
        f"سلام {user.first_name} 👋\nبه ربات تورهای گردشگری برترگشت خوش اومدی!\n\n"
        "کافیه نام مقصدت رو بفرستی تا ارزان‌ترین تورها رو پیشنهاد بدم 🌍"
    )

# پاسخ به پیام‌ها (تور یا سوال)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    user = update.message.from_user.username or update.message.from_user.first_name

    # ذخیره لید در دیتابیس
    cursor.execute("INSERT INTO leads (username, message) VALUES (?, ?)", (user, text))
    conn.commit()

    # بررسی تور در فایل JSON
    results = [t for t in tours if text in t["destination"].lower()]

    if results:
        response = "✅ تورهای پیشنهادی:\n\n"
        for t in results:
            response += f"🏖 {t['destination']}\n💰 قیمت: {t['price']}\n⭐ رضایت: {t['rating']}\n📅 تاریخ: {t['date']}\n\n"
        await update.message.reply_text(response)
        return

    # اگر تور پیدا نشد، از هوش مصنوعی بپرس
    await update.message.reply_text("🔍 در حال جستجوی اطلاعات...")
    ai_response = ask_openai(text)
    await update.message.reply_text(ai_response)

# پاسخ با OpenAI
def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "تو دستیار سفر هستی. کاربر درباره تورها، مقصدها یا سفر سوال می‌پرسه."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.7
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"⚠️ خطا در ارتباط با هوش مصنوعی: {str(e)}"

# ----------------- اجرای ربات -----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ ربات برترگشت فعال شد...")
    app.run_polling()
