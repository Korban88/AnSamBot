import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from handlers import start_handler, button_handler, message_handler
from utils import schedule_daily_signal_check
from config import TELEGRAM_BOT_TOKEN, OWNER_ID

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Обработка команд и кнопок
    app.add_handler(start_handler)         # /start
    app.add_handler(button_handler)        # inline-кнопки под сообщением
    app.add_handler(message_handler)       # reply-кнопки в панели

    # Планировщик сигнала в 8:00
    schedule_daily_signal_check(app, OWNER_ID)

    print("✅ Бот успешно запущен.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
