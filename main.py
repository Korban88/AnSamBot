import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start_handler, button_handler, handle_text_message
from utils import schedule_daily_signal_check
from config import TELEGRAM_BOT_TOKEN, OWNER_ID

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(start_handler)
    app.add_handler(button_handler)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))

    # Планировщик ежедневного сигнала
    schedule_daily_signal_check(app, OWNER_ID)

    print("🚀 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
