from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from analysis import analyze_cryptos
from utils import send_signal_message, reset_cache, debug_cache_message, debug_analysis_message
from tracking import CoinTracker
from config import TELEGRAM_BOT_TOKEN, OWNER_ID
import json
import os

# --- /start handler ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("\ud83d\udcc8 Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("\ud83d\udd04 Сбросить кеш", callback_data="reset_cache")],
        [InlineKeyboardButton("\u26d4 Остановить все отслеживания", callback_data="stop_tracking")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=reply_markup
    )

start_handler = CommandHandler("start", start)
debug_handler = CommandHandler("debug_cache", lambda update, context: debug_cache_message(update.effective_user.id, context))
debug_analysis_handler = CommandHandler("debug_analysis", lambda update, context: debug_analysis_message(update.effective_user.id, context))

# --- inline buttons handler ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "get_signal":
        await send_signal_message(user_id, context)
    elif query.data == "reset_cache":
        reset_cache()
        await query.edit_message_text("\u2705 Кеш сброшен.")
    elif query.data == "stop_tracking":
        CoinTracker.clear_all()
        await query.edit_message_text("\u26d4 Отслеживание монет остановлено.")
    elif query.data.startswith("track_"):
        symbol = query.data.split("_", 1)[1]
        CoinTracker.track(user_id, symbol, context)
        await query.edit_message_text(f"\ud83d\udd14 Монета {symbol.upper()} добавлена в отслеживание.")

button_handler = CallbackQueryHandler(button_callback)

# --- reply кнопки ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_id = update.effective_user.id

    if "сигнал" in text:
        await send_signal_message(user_id, context)
    elif "стоп" in text or "отмена" in text:
        CoinTracker.clear_all()
        await update.message.reply_text("\u26d4 Все отслеживания остановлены.")
    elif "сброс" in text:
        reset_cache()
        await update.message.reply_text("\u2705 Кеш сброшен.")
    else:
        await update.message.reply_text("\u2709\ufe0f Напиши 'сигнал', 'стоп' или 'сброс', чтобы начать.")
