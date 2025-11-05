import os, logging, base64, hashlib, json, uuid
from fastapi import FastAPI, Request, Form
from dotenv import load_dotenv
from telegram import Update

# Завантажуємо змінні середовища з .env (для локального запуску)
load_dotenv()

# Ініціалізація логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Імпортуємо об'єкт застосунку бота та функції LiqPay з відповідних модулів
from bot import application  # Application (бот) з налаштованими хендлерами
from liqpay import generate_payment_link, verify_liqpay_callback

# Створюємо FastAPI застосунок
app = FastAPI()

# Подія запуску сервера: встановлення webhook для бота і старт бот-застосунку
@app.on_event("startup")
async def on_startup():
    # Формуємо повний URL для webhook (домен+шлях)
    webhook_url = os.environ.get("DOMAIN") + os.environ.get("WEBHOOK_PATH")
    try:
        # Встановлюємо webhook Telegram бота на наш URL
        await application.bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        logger.info(f"Successfully set Telegram webhook to {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to set Telegram webhook: {e}")
    # Запускаємо бот-застосунок (починає обробляти чергу оновлень)
    await application.start()
    logger.info("Telegram bot application started.")

@app.on_event("shutdown")
async def on_shutdown():
    # Зупиняємо бот-застосунок при завершенні роботи сервера
    await application.stop()
    logger.info("Telegram bot application stopped.")

# Маршрут для прийому Telegram webhook-запитів
@app.post(os.environ.get("WEBHOOK_PATH"))
async def telegram_webhook(request: Request):
    """Обробка вхідного оновлення від Telegram (webhook)."""
    data = await request.json()
    # Конвертуємо JSON в об'єкт Update
    update = Update.de_json(data, application.bot)
    # Передаємо Update у чергу для асинхронної обробки ботом
    await application.update_queue.put(update)
    logger.info(f"Update received and enqueued (update_id={update.update_id})")
    return {"ok": True}

# Маршрут для прийому callback-запитів від LiqPay про результат платежу
@app.post("/liqpay/callback")
async def liqpay_callback(data: str = Form(...), signature: str = Form(...)):
    """
    Обробка callback від LiqPay. Перевіряє підпис та відправляє підтвердження користувачу.
    """
    logger.info("Received LiqPay callback")
    # Верифікуємо підпис і декодуємо дані
    result = verify_liqpay_callback(data, signature)
    if not result:
        logger.warning("Invalid LiqPay callback signature or data")
        return {"ok": False}
    # Отримуємо статус платежу та order_id
    status = result.get("status")
    order_id = result.get("order_id")
    logger.info(f"LiqPay payment status: {status}, order_id: {order_id}")
    # Витягуємо chat_id з order_id (ми вклали його при генерації платежу)
    chat_id = None
    if order_id:
        # припускаємо, що order_id починається з chat_id
        id_str = order_id.split("_")[0]
        if id_str.lstrip("-").isdigit():
            chat_id = int(id_str)
    # Якщо вдалося визначити chat_id, надсилаємо користувачу підтвердження
    if chat_id:
        msg_text = (f"Платіж на суму {result.get('amount')} {result.get('currency')} "
                    f"отримано, статус транзакції: {status}")
        try:
            await application.bot.send_message(chat_id=chat_id, text=msg_text)
            logger.info(f"Payment confirmation sent to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send confirmation to chat {chat_id}: {e}")
    return {"ok": True}
