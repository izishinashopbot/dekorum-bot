# liqpay.py
import os
import json
import base64
import hashlib
from dotenv import load_dotenv

load_dotenv()

PUBLIC_KEY  = os.getenv("LIQPAY_PUBLIC_KEY", "")
PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY", "")
PRICE_UAH   = int(os.getenv("PRICE_UAH", "490"))

def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")

def _sign(data_b64: str) -> str:
    sha1 = hashlib.sha1((PRIVATE_KEY + data_b64 + PRIVATE_KEY).encode("utf-8")).digest()
    return base64.b64encode(sha1).decode("ascii")

def build_checkout_payload(user_id: int, order_id: int, server_url: str, result_url: str) -> dict:
    """
    Повертає dict з полями 'data' і 'signature' для форми POST на https://www.liqpay.ua/api/3/checkout
    """
    payload = {
        "public_key": PUBLIC_KEY,
        "version": 3,
        "action": "pay",
        "amount": PRICE_UAH,
        "currency": "UAH",
        "description": f"Dekorum: доступ до каналу для user {user_id}",
        "order_id": str(order_id),
        "server_url": server_url,   # бекенд-колбек (наш /liqpay/callback)
        "result_url": result_url,   # куди повертаємо користувача після оплати
        # Режим пісочниці можна вмикати на час перевірки:
        # "sandbox": 1,
    }
    data_b64 = _b64(json.dumps(payload, ensure_ascii=False))
    signature = _sign(data_b64)
    return {"data": data_b64, "signature": signature}

def verify_callback(data_b64: str, signature: str) -> bool:
    """Перевірка, що підпис від LiqPay правильний."""
    return _sign(data_b64) == signature
