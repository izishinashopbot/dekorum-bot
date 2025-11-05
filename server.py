import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters

# Завантажуємо змінні середовища із файлу .env
load_dotenv()

# Отримуємо значення токенів і URL з середовища
BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")
APP_URL = os.getenv("APP_URL")

# Перевіримо наявність необхідних змінних
if not BOT_TOKEN or not PAYMENT_TOKEN or not APP_URL:
    raise RuntimeError("Відсутні необхідні налаштування в .env (BOT_TOKEN, PAYMENT_PROVIDER_TOKEN, APP_URL)")

# Налаштування логування (за бажанням можна увімкнути дебаг-рівень)
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # приглушуємо детальні логи HTTP

# Імпортуємо обробники з bot.py
from bot import start, buy, precheckout, successful_payment

# Створюємо екземпляр Application (асинхронного Telegram-бота)
application = Application.builder().token(BOT_TOKEN).build()

# Реєструємо обробники команд та повідомлень
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(buy, pattern="^buy$"))
application.add_handler(PreCheckoutQueryHandler(precheckout))
application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

# Параметри для вебхука
PORT = int(os.environ.get("PORT", "8443"))
# Формуємо повний URL для вебхука: <APP_URL>/<BOT_TOKEN>
WEBHOOK_PATH = "/" + BOT_TOKEN
WEBHOOK_URL = APP_URL.rstrip("/") + WEBHOOK_PATH

# Запускаємо бот з webhook (слухає на порті PORT)
application.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=BOT_TOKEN,
    webhook_url=WEBHOOK_URL,
    drop_pending_updates=True
)
