# Dekorum Telegram Bot

Telegram-бот для автоматичного доступу до приватного каналу після оплати через LiqPay.

## Функції

- Кнопка оплати в боті
- Генерація замовлення
- Перехід на оплату LiqPay
- Автоматичне підтвердження запиту на вступ у канал після успішного платежу
- Логування та контроль платежів
- Розгорнуто на Render.com

## Технології

- Python 3
- Flask
- python-telegram-bot v20
- LiqPay API
- SQLite DB
- Render (Hosting)

## Запуск локально

```bash
pip install -r requirements.txt
python server.py
