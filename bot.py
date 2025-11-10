import os
import json
import sqlite3
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# بارگذاری متغیرهای محیطی
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# دیتابیس لیدها
conn = sqlite3.connect("leads.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS leads
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT,
                   message TEXT)''')
conn.commit()

# بارگذاری داده تورها
with open("tours.json", "r", encoding="utf-8") as f:
    tours = json.load(f)

# توابع کمکی
def search_tours(keyword):
    results = []
    key = keyword.lower()
    for tour in tours:
        if key in tour["destination"].lower() or key in tour["category"].lower():
            results.append(tour)
    return results

def format_tour(tour):
    return (f"🏖 مقصد: {tour['destination']}\n"
            f"💰 قیمت: {tour['price']:,} تومان\n"
            f"🕓 مدت: {tour['duration']}\n"
            f"⭐ رضایت: {tour['satisfaction']}/5\n"
            f"📋 جزئیات: {tour['details']}")

# هندلرها
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 سلام! خوش اومدی به ربات رسمی برترگشت ✈️\n"
        "می‌خوای ارزون‌ترین تورها رو ببینی یا جستجوی مقصد کنی؟"
    )
    keyboard = [
        [InlineKeyboardButton("💸 ارزون‌ترین تورها", callback_data="cheap")],
        [InlineKeyboardButton("⭐ تورهای محبوب", callback_data="top")],
        [InlineKeyboardButton("🔍 جستجوی مقصد خاص", callback_data="search")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cheap":
        sorted_tours = sorted(tours, key=lambda x: x["price"])
        reply = "\n\n".join(format_tour(t) for t in sorted_tours[:3])
        await query.message.reply_text(f"💰 ارزون‌ترین تورها:\n\n{reply}")
    elif query.data == "top":
        sorted_tours = sorted(tours, key=lambda x: x["satisfaction"], reverse=True)
        reply = "\n\n".join(format_tour(t) for t in sorted_tours[:3])
        await query.message.reply_text(f"⭐ تورهای پررضایت:\n\n{reply}")
    elif query.data == "search":
        await query.message.reply_text("📍 لطفاً مقصد یا کشور مورد نظرت رو بنویس:")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    username = update.message.from_user.username or ""
    cursor.execute("INSERT INTO leads (username, message) VALUES (?, ?)", (username, user_text))
    conn.commit()
    results = search_tours(user_text)
    if results:
        reply = "\n\n".join(format_tour(t) for t in results)
        await update.message.reply_text(f"🧭 نتایج برای '{user_text}':\n\n{reply}")
    else:
        await update.message.reply_text("😔 متأسفانه چیزی پیدا نشد. لطفاً مقصد دیگری امتحان کن.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("می‌تونی به‌صورت ساده بنویسی مثل: «تور ارزان ترکیه» یا «تور لوکس دبی»")

def main():
    if not TELEGRAM_TOKEN:
        print("❌ خطا: توکن تلگرام در فایل .env پیدا نشد!")
        return
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("✅ ربات @bartargashtbot در حال اجراست…")
    app.run_polling()

if __name__ == "__main__":
    main()