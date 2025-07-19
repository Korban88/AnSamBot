import asyncio
import logging
from telegram.ext import ApplicationBuilder
from handlers import start_handler, button_callback_handler
from scheduler import schedule_daily_signal_check
from config import TELEGRAM_BOT_TOKEN, OWNER_ID
import nest_asyncio

nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация хендлеров
    app.add_handler(start_handler)
    app.add_handler(button_callback_handler)

    # Планирование ежедневной отправки сигнала в 08:00
    schedule_daily_signal_check(app, OWNER_ID)

    print("Бот запущен.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
