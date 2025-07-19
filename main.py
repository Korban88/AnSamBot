import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
from handlers import start_handler, button_callback_handler

TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"

# Основные кнопки
keyboard = [
    [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
    [InlineKeyboardButton("Сбросить кэш", callback_data="reset_cache")],
    [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")]
]
markup = InlineKeyboardMarkup(keyboard)

async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=markup
    )

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", command_start))
    app.add_handler(CallbackQueryHandler(button_callback_handler))

    print("Бот запущен.")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(main())
        else:
            raise
