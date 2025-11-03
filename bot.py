# bot.py
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from db import create_order, save_join_request

load_dotenv()

logging.basicConfig(level=logging.INFO)
logging.getLogger("telegram").setLevel(logging.INFO)
logging.getLogger("telegram.ext").setLevel(logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRICE_UAH = int(os.getenv("PRICE_UAH", "490"))
APP_URL   = os.getenv("APP_URL", "").rstrip("/")

if not BOT_TOKEN:
    raise RuntimeError("ENV BOT_TOKEN is not set")

APP = Application.builder().token(BOT_TOKEN).build()

# /start
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("💳 Оплатити", callback_data="pay")]]
    await update.message.reply_text(
        f"Привіт! Доступ до каналу — {PRICE_UAH} грн.\n"
        f"1) Натисни «Оплатити»\n"
        f"2) Після оплати подай запит на вступ у канал (Request to Join)\n"
        f"3) Бот схвалить запит автоматично ✅",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# натискання «Оплатити»
async def on_pay_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = update.effective_user.id
    order_id = create_order(user_id=user_id)
    save_join_request(order_id=order_id, user_id=user_id)

    pay_url = f"{APP_URL}/pay/{order_id}"
    await q.edit_message_text(
        f"💳 Сума до оплати: {PRICE_UAH} грн\n"
        f"Перейдіть за посиланням для оплати:\n{pay_url}\n\n"
        f"Після оплати натисніть «Request to Join» у каналі — бот схвалить автоматично."
    )

APP.add_handler(CommandHandler("start", cmd_start))
APP.add_handler(CallbackQueryHandler(on_pay_click, pattern="^pay$"))
