from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from analysis import analyze_cryptos
from utils import (
    send_signal_message,
    reset_cache,
    debug_cache_message,
    debug_analysis_message,
    save_signal_cache,
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

# Команда /analyze — запускает анализ и обновляет кэш
async def analyze_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await manual_refresh_signals(update.effective_user.id, context)

# Debug команды
analyze_command_handler = CommandHandler("analyze", analyze_handler)
debug_handler = CommandHandler("debug_cache", lambda update, context: debug_cache_message(update.effective_user.id, context))
debug_analysis_handler = CommandHandler("debug_analysis", lambda update, context: debug_analysis_message(update.effective_user.id, context))
start_handler = CommandHandler("start", start)

# Inline кнопки
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "get_signal":
        await send_signal_message(user_id, context)
    elif query.data == "reset_cache":
        reset_cache()
        await query.edit_message_text("✅ Кеш сброшен.")
    elif query.data == "stop_tracking":
        CoinTracker.clear_all()
        await query.edit_message_text("⛔ Отслеживание монет остановлено.")
    elif query.data == "debug_cache":
        await debug_cache_message(user_id, context)
    elif query.data == "debug_analysis":
        await debug_analysis_message(user_id, context)
    elif query.data.startswith("track_"):
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
    elif "сигнал" in text:
        await send_signal_message(user_id, context)
    elif "стоп" in text or "отмена" in text:
        CoinTracker.clear_all()
        await update.message.reply_text("⛔ Все отслеживания остановлены.", reply_markup=reply_markup)
    elif "сброс" in text:
        reset_cache()
        await update.message.reply_text("✅ Кеш сброшен.", reply_markup=reply_markup)
    elif "анализ" in text:
        await debug_analysis_message(user_id, context)
    elif "кеш" in text:
        await debug_cache_message(user_id, context)
    else:
        await update.message.reply_text("✉️ Напиши 'сигнал', 'стоп', 'анализ' или 'сброс', чтобы начать.", reply_markup=reply_markup)
