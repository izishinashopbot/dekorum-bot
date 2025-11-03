# server.py
import os
import asyncio
import logging
import base64
import json

from dotenv import load_dotenv
from flask import Flask, request, abort, render_template_string
from telegram import Update
from telegram.error import Forbidden

from bot import APP as tg_app
from db import get_order, set_order_status, pop_join_request, create_order
from liqpay import build_checkout_payload, verify_callback

# ── базові налаштування
load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("server")

WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")
APP_URL       = os.getenv("APP_URL", "").rstrip("/")
CHANNEL_ID    = int(os.getenv("CHANNEL_ID", "0"))

if not WEBHOOK_SECRET:
    raise RuntimeError("ENV TELEGRAM_WEBHOOK_SECRET is not set")
if not APP_URL:
    raise RuntimeError("ENV APP_URL is not set")

# (a) одноразова ініціалізація PTB Application
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Відправляє привітання та кнопку LiqPay-оплати."""
    keyboard = [
        [InlineKeyboardButton("💳 Сплатити 1 грн", callback_data="buy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard )
        await tg_app.process_update(update)
    except Forbidden:
        pass
    except Exception as e:
        log.exception("Update handling failed: %s", e)

app = Flask(__name__)

# ── healthcheck
@app.get("/")
def index():
    return "OK", 200

# ── Telegram webhook
@app.post(f"/tg/{WEBHOOK_SECRET}")
def tg_webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        abort(400)
    try:
        update = Update.de_json(data, tg_app.bot)
    except Exception as e:
        log.exception("Failed to parse Update: %s", e)
        abort(400)

    # event loop для тасок
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def _process():
        try:
            # (b) гарантуємо ініціалізацію
           await ensure_app_ready()
log.info("App initialized OK")
log.info("Processing update: msg=%s cq=%s",
         bool(update.message), bool(update.callback_query))

            
            await tg_app.process_update(update)
        except Forbidden:
            pass
        except Exception as e:
            log.exception("Update handling failed: %s", e)

    loop.create_task(_process())
    return "OK", 200

# ── сторінка оплати (автосабміт)
PAY_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Оплата</title></head>
<body>
<form id="f" method="POST" action="https://www.liqpay.ua/api/3/checkout">
  <input type="hidden" name="data" value="{{ data }}">
  <input type="hidden" name="signature" value="{{ signature }}">
  <noscript><button type="submit">Перейти до оплати</button></noscript>
</form>
<script>document.getElementById('f').submit();</script>
</body></html>
"""

@app.get("/pay/<int:order_id>")
def pay(order_id: int):
    if not get_order(order_id):
        order_id = create_order(user_id=0)
    payload = build_checkout_payload(
        user_id=0,
        order_id=order_id,
        server_url=f"{APP_URL}/liqpay/callback",
        result_url=f"{APP_URL}/paid/{order_id}",
    )
    return render_template_string(PAY_HTML, **payload)

# ── колбек від LiqPay
@app.post("/liqpay/callback")
def liqpay_callback():
    data_b64  = request.form.get("data", "")
    signature = request.form.get("signature", "")
    if not data_b64 or not signature or not verify_callback(data_b64, signature):
        abort(400)

    payload  = json.loads(base64.b64decode(data_b64).decode("utf-8"))
    order_id = int(payload.get("order_id", "0") or 0)
    status   = payload.get("status", "")

    log.info("LiqPay callback: order=%s status=%s", order_id, status)

    if status in {"success", "sandbox", "sandbox_success", "subscribed", "hold_approved"}:
        set_order_status(order_id, "paid")
        user_id = pop_join_request(order_id)
        if user_id and CHANNEL_ID:
            async def _approve():
                try:
                    await ensure_app_ready()
                    await tg_app.bot.approve_chat_join_request(CHANNEL_ID, user_id)
                except Exception as e:
                    log.exception("approve_chat_join_request failed: %s", e)

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.create_task(_approve())

    return "OK", 200

# ── сторінка після оплати
@app.get("/paid/<int:order_id>")
def paid(order_id: int):
    return (
        f"Оплата прийнята (замовлення #{order_id}). "
        f"Подайте Request to Join у каналі — бот схвалить автоматично.",
        200,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
