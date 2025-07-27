import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start_handler, button_handler, message_handler
from utils import schedule_daily_signal_check, debug_cache_message, debug_analysis_message
from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from telegram import ReplyKeyboardMarkup


reply_keyboard = ReplyKeyboardMarkup([
    ["📈 Получить сигнал"],
    ["♻️ Сбросить кеш"],
    ["⛔ Остановить все отслеживания"],
    ["📦 Кеш сигналов"],
    ["📊 Анализ монет"]
], resize_keyboard=True)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    # reply кнопки
    async def reply_panel(update, context):
        text = update.message.text
        if text == "📈 Получить сигнал":
            from utils import send_signal_message
            await send_signal_message(update.effective_chat.id, context)
        elif text == "♻️ Сбросить кеш":
            from utils import reset_cache
            reset_cache()
            await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Кеш сброшен.")
        elif text == "⛔ Остановить все отслеживания":
            from tracking import stop_all_trackers
            await stop_all_trackers(update.effective_chat.id)
        elif text == "📦 Кеш сигналов":
            await debug_cache_message(update.effective_chat.id, context)
        elif text == "📊 Анализ монет":
            await debug_analysis_message(update.effective_chat.id, context)

    app.add_handler(MessageHandler(filters.TEXT, reply_panel))

    schedule_daily_signal_check(app, OWNER_ID)

    print("🚀 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
