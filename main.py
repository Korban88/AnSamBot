import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start_handler, button_handler, message_handler
from utils import schedule_daily_signal_check
from config import TELEGRAM_BOT_TOKEN, OWNER_ID

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Обработчики команд и сообщений
    app.add_handler(start_handler)               # /start
    app.add_handler(button_handler)              # inline-кнопки под сообщениями
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))  # обычные текстовые сообщения

    # Планировщик: ежедневный сигнал в 8:00
    schedule_daily_signal_check(app, OWNER_ID)

    print("✅ Бот успешно запущен.")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
