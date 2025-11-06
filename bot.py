import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes

# Унікальний payload для платежу (використовується для перевірки)
PAYLOAD = "LiqPayTestInvoice"

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Відправляє привітання та кнопку LiqPay-оплати."""
    keyboard = [
        [InlineKeyboardButton("💳 Сплатити 1 грн", callback_data="buy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Надсилаємо повідомлення з кнопкою оплати
    await update.message.reply_text(
        "Привіт! Натисни кнопку нижче, щоб здійснити платіж через LiqPay.",
        reply_markup=reply_markup
    )

# Обробник callback від натискання кнопки "сплатити"
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає інвойс (рахунок) для оплати при натисканні кнопки."""
    query = update.callback_query
    await query.answer()  # підтверджуємо callback, щоб прибрати "годинник"
    chat_id = update.effective_chat.id

    # Параметри рахунку (інвойсу)
    title = "Тестовий платіж"
    description = "Оплата тестового товару через LiqPay"
    # Валюта та сума
    currency = "UAH"
    price = 1  # 1 гривня
    prices = [LabeledPrice(label="Тестовий товар", amount=price * 100)]  # 100 копійок = 1 грн

    # Надсилаємо рахунок на оплату (invoice) користувачу
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=PAYLOAD,
        provider_token=os.getenv("PAYMENT_PROVIDER_TOKEN"),
        currency=currency,
        prices=prices,
        # Вимкнено запит адреси доставки, телефон тощо для спрощення
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False
    )

# Обробник PreCheckoutQuery – фінальний крок перед підтвердженням оплати
async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Відповідає на запит перед підтвердженням оплати (PreCheckoutQuery)."""
    query = update.pre_checkout_query
    if query.invoice_payload != PAYLOAD:
        # Якщо payload не співпадає з нашим – відхиляємо оплату
        await query.answer(ok=False, error_message="Щось пішло не так з PAYLOAD...")
    else:
        # Підтверджуємо, що все гаразд для завершення оплати
        await query.answer(ok=True)

# Обробник повідомлення про успішну оплату
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає повідомлення подяки після успішного платежу."""
    await update.message.reply_text("Дякуємо за оплату! ✅ Ваш платіж отримано.")
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

application = ApplicationBuilder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(buy, pattern="^buy$"))
application.add_handler(PreCheckoutQueryHandler(precheckout))
application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
