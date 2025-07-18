import logging
from telegram import BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN
from handlers import (
    start_handler,
    get_signal_handler,
    follow_coin_handler,
    stop_tracking_handler,
    reset_cache_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def set_bot_commands(application: Application):
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("get_signal", "Получить сигнал"),
        BotCommand("stop_tracking", "Остановить все отслеживания"),
        BotCommand("reset_cache", "Сбросить кеш"),
    ]
    await application.bot.set_my_commands(commands)

def setup_application() -> Application:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("get_signal", get_signal_handler))
    application.add_handler(CommandHandler("stop_tracking", stop_tracking_handler))
    application.add_handler(CommandHandler("reset_cache", reset_cache_handler))

    application.add_handler(CallbackQueryHandler(follow_coin_handler, pattern="^follow_"))

    application.post_init(set_bot_commands)

    return application

if __name__ == "__main__":
    app = setup_application()
    logger.info("🚀 Бот запущен")
    app.run_polling()
