import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from db import create_order, save_join_request

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRICE_UAH = int(os.getenv("PRICE_UAH", "490"))
APP_URL   = os.getenv("APP_URL", "").rstrip("/")

# --- Application (експорт для server.py) ---
APP = Application.builder().token(BOT_TOKEN).build()

# --- /start ---
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("💳 Оплатити", callback_data="pay")]]
    await update.message.reply_text(
        f"Привіт! Доступ до каналу — {PRICE_UAH} грн.\nНатисни «Оплатити», щоб перейти до LiqPay.",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# --- Клік «Оплатити» ---
async def on_pay_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    order_id = create_order(user_id=user_id)           # створили замовлення
    save_join_request(order_id=order_id, user_id=user_id)  # запам’ятали хто чекає доступу

    pay_url = f"{APP_URL}/pay/{order_id}"
    await query.edit_message_text(
        f"💳 Сума до оплати: {PRICE_UAH} грн\n"
        f"Перейдіть за посиланням для оплати:\n{pay_url}"
    )

# --- реєстрація хендлерів ---
APP.add_handler(CommandHandler("start", cmd_start))
APP.add_handler(CallbackQueryHandler(on_pay_click, pattern="^pay$"))
