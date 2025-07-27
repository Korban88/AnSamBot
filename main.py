import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from handlers import (
    start_handler,
    button_handler,
    handle_text_message,
    analyze_command_handler
)
from utils import schedule_daily_signal_check
from config import TELEGRAM_BOT_TOKEN, OWNER_ID

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Обработчики команд
    app.add_handler(start_handler)
    app.add_handler(analyze_command_handler)  # /analyze для ручного запуска анализа
    app.add_handler(button_handler)  # inline кнопки
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))  # reply кнопки

    # Планировщик сигнала в 8:00
    schedule_daily_signal_check(app, OWNER_ID)

    print("🚀 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    asyncio.get_event_loop().run_until_complete(main())
