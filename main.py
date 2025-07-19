import asyncio
import nest_asyncio
from telegram.ext import ApplicationBuilder
from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from handlers import start_handler, button_handler
from scheduler import schedule_daily_signal_check

nest_asyncio.apply()

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавление обработчиков
    app.add_handler(start_handler)
    app.add_handler(button_handler)

    # Планировщик сигнала в 8:00
    schedule_daily_signal_check(app, OWNER_ID)

    print("Бот запущен.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
