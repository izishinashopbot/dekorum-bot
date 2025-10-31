# bot.py
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
logging.basicConfig(level=logging.INFO)
logging.getLogger("telegram").setLevel(logging.INFO)
logging.getLogger("telegram.ext").setLevel(logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRICE_UAH = int(os.getenv("PRICE_UAH", "490"))
APP_URL   = os.getenv("APP_URL", "").rstrip("/")

APP = Application.builder().token(BOT_TOKEN).build()

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("💳 Оплатити", callback_data="pay")]]
    await update.message.reply_text(
        f"Привіт! Доступ до каналу — {PRICE_UAH} грн.\nНатисни «Оплатити».",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def on_pay_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        f"Сума: {PRICE_UAH} грн\nПерейдіть за посиланням для оплати:\n{APP_URL}/pay/TEST"
    )

APP.add_handler(CommandHandler("start", cmd_start))
APP.add_handler(CallbackQueryHandler(on_pay_click, pattern="^pay$"))
