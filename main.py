from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import BOT_TOKEN
from handlers import (
    start_handler,
    get_signal_handler,
    follow_coin_handler,
    stop_tracking_handler,
    reset_cache_handler,
)

def setup_application():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("get_signal", get_signal_handler))
    application.add_handler(CommandHandler("stop_tracking", stop_tracking_handler))
    application.add_handler(CommandHandler("reset_cache", reset_cache_handler))

    # Регистрация callback кнопок
    application.add_handler(CallbackQueryHandler(follow_coin_handler, pattern="^follow_"))
    application.add_handler(CallbackQueryHandler(stop_tracking_handler, pattern="^stop_tracking$"))
    application.add_handler(CallbackQueryHandler(reset_cache_handler, pattern="^reset_cache$"))
    application.add_handler(CallbackQueryHandler(get_signal_handler, pattern="^get_signal$"))

    return application

if __name__ == "__main__":
    app = setup_application()
    app.run_polling()
