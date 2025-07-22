import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start_handler, button_handler, message_handler
from utils import schedule_daily_signal_check
from config import TELEGRAM_BOT_TOKEN

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(start_handler)
    app.add_handler(button_handler)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    schedule_daily_signal_check(app)

    print("Бот запущен.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
