import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN
from handlers import start_handler, get_signal_handler, follow_coin_handler, stop_tracking_handler, reset_cache_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_application() -> Application:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("get_signal", get_signal_handler))
    application.add_handler(CommandHandler("stop_tracking", stop_tracking_handler))
    application.add_handler(CommandHandler("reset_cache", reset_cache_handler))

    application.add_handler(CallbackQueryHandler(get_signal_handler, pattern="^get_signal$"))
    application.add_handler(CallbackQueryHandler(stop_tracking_handler, pattern="^stop_tracking$"))
    application.add_handler(CallbackQueryHandler(reset_cache_handler, pattern="^reset_cache$"))
    application.add_handler(CallbackQueryHandler(follow_coin_handler, pattern="^follow_"))

    return application

if __name__ == "__main__":
    app = setup_application()
    logger.info("🚀 Бот запущен")
    app.run_polling()
