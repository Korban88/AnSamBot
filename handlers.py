from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from utils import send_signal_message, reset_cache
from tracking import start_tracking, stop_all_trackings
from config import tracked_symbols

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['📈 Получить сигнал'], ['❌ Остановить все отслеживания'], ['🔁 Сбросить кеш']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать в AnSam Bot", reply_markup=reply_markup)

start_handler = CommandHandler("start", start)

# Inline кнопки под сообщением
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("track_"):
        symbol = query.data.replace("track_", "")
        if symbol in tracked_symbols:
            await start_tracking(context, query.message.chat_id, symbol)
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(f"⏱ Отслеживание {symbol} запущено.")
        else:
            await query.message.reply_text("Монета не поддерживается для отслеживания.")
    elif query.data == "stop_all":
        await stop_all_trackings()
        await query.message.reply_text("🛑 Все отслеживания остановлены.")

button_handler = CallbackQueryHandler(button_callback)

# Reply кнопки внизу
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()

    if "получить сигнал" in text:
        await send_signal_message(update.message.chat_id, context)
    elif "остановить" in text:
        await stop_all_trackings()
        await update.message.reply_text("🛑 Все отслеживания остановлены.")
    elif "сбросить кеш" in text:
        reset_cache()
        await update.message.reply_text("♻️ Кеш сброшен.")
    else:
        await update.message.reply_text("Выберите одну из команд.")

message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
