# main.py - ربات فروشگاه تلگرام

import os
import json
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = os.getenv("BOT_TOKEN")
ORDERS_FILE = "orders.json"

PRODUCTS = [
    {
        "id": 1,
        "name": "دوره آموزش پایتون",
        "price": "399,000 تومان",
        "description": "دوره کامل پایتون برای مبتدیان تا پیشرفته."
    },
    {
        "id": 2,
        "name": "کتاب الکترونیکی بازاریابی",
        "price": "149,000 تومان",
        "description": "راهنمای عملی برای رشد در فضای مجازی."
    }
]

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_order(order):
    orders = load_orders()
    order["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    orders.append(order)
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🛒 محصولات", "📞 تماس با ما"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "سلام به فروشگاه هوشمند ما خوش آمدید! 🌟\n"
        "از منوی زیر استفاده کنید:",
        reply_markup=reply_markup
    )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "📌 محصولات ما:\n\n"
    for p in PRODUCTS:
        message += (
            f"🔹 <b>{p['name']}</b>\n"
            f"💰 قیمت: {p['price']}\n"
            f"📝 شرح: {p['description']}\n"
            f"📦 کد: <code>{p['id']}</code>\n\n"
        )
    message += "برای سفارش، کد محصول رو ارسال کنید."
    await update.message.reply_html(message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "🛒 محصولات":
        await show_products(update, context)
        return ConversationHandler.END
    elif text == "📞 تماس با ما":
        await update.message.reply_text("📞 شماره تماس: 09123456789\n📧 ایمیل: info@shop.com")
        return ConversationHandler.END

    if text.isdigit():
        product_id = int(text)
        product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if product:
            context.user_data['pending_order'] = product
            await update.message.reply_html(
                f"شما محصول زیر رو انتخاب کردید:\n\n"
                f"📦 <b>{product['name']}</b>\n"
                f"💰 {product['price']}\n\n"
                "لطفاً نام و نام خانوادگی خود را وارد کنید:"
            )
            return AWAITING_NAME
        else:
            await update.message.reply_text("❌ محصولی با این کد یافت نشد.")
    return ConversationHandler.END

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['customer_name'] = update.message.text
    await update.message.reply_text("ممنون! حالا لطفاً شماره تماس خود را وارد کنید:")
    return AWAITING_PHONE

async def get_phone_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    name = context.user_data['customer_name']
    product = context.user_data['pending_order']

    order = {
        "product_id": product["id"],
        "product_name": product["name"],
        "price": product["price"],
        "customer_name": name,
        "phone": phone
    }
    save_order(order)

    await update.message.reply_html(
        f"✅ سفارش شما با موفقیت ثبت شد!\n\n"
        f"📦 محصول: <b>{product['name']}</b>\n"
        f"👤 نام: {name}\n"
        f"📞 تماس: {phone}\n"
        f"💰 قیمت: {product['price']}\n\n"
        "به زودی با شما تماس خواهیم گرفت.\n"
        "ممنون از خرید شما 🌟"
    )
    context.user_data.clear()
    return ConversationHandler.END

AWAITING_NAME, AWAITING_PHONE = range(2)

def main():
    if not TOKEN:
        print("❌ BOT_TOKEN یافت نشد! به تنظیمات در Railway برو.")
        return

    print("🤖 ربات در حال اجراست...")
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={
            AWAITING_NAME: [MessageHandler(filters.TEXT, get_name)],
            AWAITING_PHONE: [MessageHandler(filters.TEXT, get_phone_and_save)]
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()