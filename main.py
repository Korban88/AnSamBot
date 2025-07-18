from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN
from handlers import (
    start_handler,
    get_signal_handler,
    follow_coin_handler,
    stop_tracking_handler,
    reset_cache_handler,
    text_message_handler
)

def setup_application():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CallbackQueryHandler(follow_coin_handler, pattern="^follow_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    return application

if __name__ == "__main__":
    app = setup_application()
    app.run_polling()
