import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)
from handlers import (
    start_handler, text_message_handler,
    button_callback_handler, reset_cache_handler
)

TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"

keyboard = [
    [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
    [InlineKeyboardButton("Сбросить кеш", callback_data="reset_cache")],
    [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")]
]

markup = InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=markup
    )

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, text_message_handler))
    app.add_handler(CallbackQueryHandler(button_callback_handler))

    print("Бот запущен.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
