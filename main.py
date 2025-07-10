# main.py (обновлённый с вызовом fetch_and_cache_indicators)

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN
from handlers import start, button_callback
from crypto_utils import fetch_and_cache_indicators
import nest_asyncio

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))

    await app.run_polling()

if __name__ == "__main__":
    fetch_and_cache_indicators()  # ключевой вызов перед стартом бота

    # Проверим, что файл indicators_cache.json действительно заполнен
    try:
        import json
        with open("indicators_cache.json", "r") as f:
            cache = json.load(f)
            print(f"\n📦 Кеш: {len(cache)} монет загружено\n")
    except Exception as e:
        print(f"❌ Ошибка при чтении кеша: {e}")

    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
