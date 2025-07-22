from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start_handler, button_handler, message_handler
from utils import schedule_daily_signal_check
from config import TELEGRAM_BOT_TOKEN, OWNER_ID

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

app.add_handler(start_handler)
app.add_handler(button_handler)
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

schedule_daily_signal_check(app, OWNER_ID)

if __name__ == "__main__":
    print("🚀 Бот запущен.")
    app.run_polling()
