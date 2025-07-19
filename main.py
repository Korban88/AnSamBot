import asyncio
from telegram.ext import ApplicationBuilder
from handlers import (
    start_command_handler,
    button_callback_handler,
    text_message_handler
)
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command_handler))
    app.add_handler(CallbackQueryHandler(button_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    print("Бот запущен.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
