from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from analysis import analyze_cryptos
from utils import send_signal_message, reset_cache
from tracking import CoinTracker
from config import TELEGRAM_BOT_TOKEN, OWNER_ID
import json
import os

# --- /start handler ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("🔄 Сбросить кеш", callback_data="reset_cache")],
        [InlineKeyboardButton("⛔ Остановить все отслеживания", callback_data="stop_tracking")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=reply_markup
    )

start_handler = CommandHandler("start", start)

# --- inline buttons handler ---
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
    elif query.data.startswith("track_"):
        symbol = query.data.split("_", 1)[1]
        CoinTracker.track(user_id, symbol, context)
        await query.edit_message_text(f"🔔 Монета {symbol.upper()} добавлена в отслеживание.")

button_handler = CallbackQueryHandler(button_callback)

# --- reply кнопки ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_id = update.effective_user.id

    if "сигнал" in text:
        await send_signal_message(user_id, context)
    elif "стоп" in text or "отмена" in text:
        CoinTracker.clear_all()
        await update.message.reply_text("⛔ Все отслеживания остановлены.")
    elif "сброс" in text:
        reset_cache()
        await update.message.reply_text("✅ Кеш сброшен.")
    else:
        await update.message.reply_text("✉️ Напиши 'сигнал', 'стоп' или 'сброс', чтобы начать.")

message_handler = handle_text_message
