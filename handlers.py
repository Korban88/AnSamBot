from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import json
import os
import asyncio

from analysis import analyze_cryptos
from tracking import start_tracking, stop_all_trackings
from utils import send_signal_message, reset_cache

# === Команда /start ===
async def start_handler_func(update: Update, context: CallbackContext):
    keyboard = [
        [KeyboardButton("📈 Получить сигнал")],
        [KeyboardButton("🛑 Остановить все отслеживания")],
        [KeyboardButton("♻️ Сбросить кеш")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup)

start_handler = CommandHandler("start", start_handler_func)

# === Inline кнопки под сообщением ===
async def button_handler_func(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("track:"):
        symbol = data.split(":")[1]
        await start_tracking(symbol, context.bot, query.message.chat_id)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"🔔 Начал отслеживать монету: {symbol}")

button_handler = CallbackQueryHandler(button_handler_func)

# === Reply кнопки в панели ===
async def message_handler(update: Update, context: CallbackContext):
    text = update.message.text

    if text == "📈 Получить сигнал":
        coins = await analyze_cryptos()

        if not coins:
            await update.message.reply_text("Сейчас нет подходящих монет по фильтрам.")
            return

        for coin in coins:
            await send_signal_message(update.effective_chat.id, context.bot, coin)
            await asyncio.sleep(1)

    elif text == "🛑 Остановить все отслеживания":
        await stop_all_trackings(update.effective_chat.id)
        await update.message.reply_text("⛔️ Все отслеживания остановлены.")

    elif text == "♻️ Сбросить кеш":
        reset_cache()
        await update.message.reply_text("🧹 Кеш успешно сброшен.")

message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler)
