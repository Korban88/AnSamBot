from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from utils import (
    send_signal_message,
    reset_cache,
    debug_cache_message,
    debug_analysis_message,
    manual_refresh_signals
)
from tracking import CoinTracker

# Панель снизу (ReplyKeyboard)
reply_keyboard = [
    [KeyboardButton("📈 Получить сигнал")],
    [KeyboardButton("🔁 Обновить сигналы"), KeyboardButton("🔁 Сбросить кеш")],
    [KeyboardButton("⛔ Остановить все отслеживания")],
    [KeyboardButton("📦 Кеш сигналов"), KeyboardButton("📊 Анализ монет")]
]
reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=reply_markup
    )

# Создаём handler для main.py
start_handler = CommandHandler("start", start)


# Inline кнопки
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith("track_"):
        symbol = query.data.split("_", 1)[1]
        CoinTracker.track(user_id, symbol, context)
        await query.edit_message_text(f"🔔 Монета {symbol.upper()} добавлена в отслеживание.")

button_handler = CallbackQueryHandler(button_callback)


# Reply кнопки
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_id = update.effective_user.id

    if "обновить" in text:
        await manual_refresh_signals(user_id, context)
    elif "сигнал" in text and "кеш" not in text:
        await send_signal_message(user_id, context)
    elif "сброс" in text:
        reset_cache()
        await update.message.reply_text("✅ Кеш сброшен.", reply_markup=reply_markup)
    elif "анализ" in text:
        await debug_analysis_message(user_id, context)
    elif "кеш" in text:
        await debug_cache_message(user_id, context)
    elif "стоп" in text or "отмена" in text:
        CoinTracker.clear_all()
        await update.message.reply_text("⛔ Все отслеживания остановлены.", reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            "✉️ Напиши 'сигнал', 'анализ', 'кеш' или 'сброс'.",
            reply_markup=reply_markup
        )
