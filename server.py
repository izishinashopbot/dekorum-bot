import os
import json
import asyncio
import base64
from dotenv import load_dotenv
from flask import Flask, request, abort, render_template_string
from telegram import Update
from telegram.error import Forbidden
from db import get_order, set_order_status, pop_join_request
from bot import APP as tg_app
from liqpay import build_checkout_payload, verify_callback
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

@app.post(f"/tg/{WEBHOOK_SECRET}")
def tg_webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        abort(400)

    update = Update.de_json(data, tg_app.bot)
    asyncio.get_event_loop().create_task(tg_app.process_update(update))
    return "OK", 200
