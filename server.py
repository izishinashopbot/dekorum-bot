import os
import asyncio
import logging

from dotenv import load_dotenv
from flask import Flask, request, abort
from telegram import Update
from telegram.error import Forbidden

# УВАЖЛИВО: у bot.py має бути створений Application як змінна APP
# приклад у bot.py:
#   from telegram.ext import Application, CommandHandler
#   APP = Application.builder().token(os.getenv("BOT_TOKEN")).build()
#   async def start(u, c): await u.message.reply_text("Привіт! Я активний ✅")
#   APP.add_handler(CommandHandler("start", start))
from bot import APP as tg_app  # <-- імпортуємо Application з bot.py


load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("server")

WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    
    raise RuntimeError("ENV TELEGRAM_WEBHOOK_SECRET is not set")

app = Flask(__name__)



@app.get("/")
def index():
    return "OK", 200


@app.post(f"/tg/{WEBHOOK_SECRET}")
def tg_webhook():
    """
    Приймаємо JSON від Telegram, перетворюємо у Update
    і віддаємо обробку Application (async).
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        abort(400)

    try:
        update = Update.de_json(data, tg_app.bot)
    except Exception as e:
        log.exception("Failed to parse Update: %s", e)
        abort(400)

    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    
    async def _process():
        try:
            await tg_app.process_update(update)
        except Forbidden:
            
            pass
        except Exception as e:
            log.exception("Update handling failed: %s", e)

    loop.create_task(_process())
    return "OK", 200



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
