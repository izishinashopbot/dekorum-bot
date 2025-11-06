import os
import json
import base64
import hashlib
from dotenv import load_dotenv

load_dotenv()

PUBLIC_KEY = os.getenv("LIQPAY_PUBLIC_KEY", "")
PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY", "")
PRICE_UAH = int(os.getenv("PRICE_UAH", "49"))


def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def _sign(data_b64: str) -> str:
    sha1 = hashlib.sha1((PRIVATE_KEY + data_b64 + PRIVATE_KEY).encode("utf-8")).digest()
    return base64.b64encode(sha1).decode("ascii")


def build_checkout_payload(user_id: int, order_id: int, server_url: str, result_url: str) -> dict:
    payload = {
        "public_key": PUBLIC_KEY,
        "version": 3,
        "action": "pay",
        "amount": PRICE_UAH,
        "currency": "UAH",
        "description": f"Оплата замовлення #{order_id}",
        "order_id": f"{user_id}_{order_id}",
        "server_url": server_url,
        "result_url": result_url,
    }

    data_b64 = _b64(json.dumps(payload))
    signature = _sign(data_b64)

    return {
        "data": data_b64,
        "signature": signature,
    }


# ⬇️ Функція 1: Генерація посилання на оплату
def generate_payment_link(user_id: int, order_id: int, server_url: str, result_url: str) -> str:
    payload = build_checkout_payload(user_id, order_id, server_url, result_url)
    return f"https://www.liqpay.ua/api/3/checkout?data={payload['data']}&signature={payload['signature']}"


# ⬇️ Функція 2: Перевірка коректності відповіді від LiqPay
def verify_liqpay_callback(data: str, signature: str) -> bool:
    expected_signature = _sign(data)
    return expected_signature == signature
