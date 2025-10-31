WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

@app.post(f"/tg/{WEBHOOK_SECRET}")
def tg_webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        abort(400)

    update = Update.de_json(data, tg_app.bot)
    asyncio.get_event_loop().create_task(tg_app.process_update(update))
    return "OK", 200
