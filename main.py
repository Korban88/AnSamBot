import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from handlers import (
    start_handler,
    button_handler,
    handle_text_message,
    analyze_command_handler
)
from utils import schedule_daily_signal_check
from scheduler import schedule_signal_refresh
from config import TELEGRAM_BOT_TOKEN, OWNER_ID

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(start_handler)
    app.add_handler(analyze_command_handler)
    app.add_handler(button_handler)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))

    schedule_daily_signal_check(app, OWNER_ID)
    schedule_signal_refresh(app)   # теперь передаем app

    print("🚀 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
