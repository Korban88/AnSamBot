import asyncio
import logging
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO)

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает!")

async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
