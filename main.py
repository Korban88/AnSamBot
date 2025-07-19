import asyncio
import nest_asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from handlers import start_handler, button_callback_handler
from scheduler import schedule_daily_signal_check

nest_asyncio.apply()  # Обход ошибки "event loop is already running"


async def main():
    print("Бот запущен.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд и кнопок
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(button_callback_handler))

    # Планировщик ежедневного сигнала в 8:00
    schedule_daily_signal_check(app, OWNER_ID)

    # Запуск бота
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
