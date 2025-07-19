from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from analysis import get_top_signal
from tracking import start_tracking, stop_all_trackings
import os

keyboard = [
    [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
    [InlineKeyboardButton("Сбросить кеш", callback_data="reset_cache")],
    [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")]
]
markup = InlineKeyboardMarkup(keyboard)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=markup
    )


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Используй кнопки ниже для работы с ботом.",
        reply_markup=markup
    )


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        signal = await get_top_signal()
        if signal:
            await query.edit_message_text(signal, reply_markup=markup, parse_mode="MarkdownV2")
        else:
            await query.edit_message_text("Не удалось получить надёжный сигнал.", reply_markup=markup)

    elif query.data == "reset_cache":
        await reset_cache_handler(update, context)

    elif query.data == "stop_tracking":
        await stop_all_trackings()
        await query.edit_message_text("⛔️ Все отслеживания остановлены.", reply_markup=markup)


async def reset_cache_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        os.remove("indicators_cache.json")
        await update.callback_query.edit_message_text("🧹 Кеш успешно сброшен.", reply_markup=markup)
    except FileNotFoundError:
        await update.callback_query.edit_message_text("🧹 Кеш уже пуст.", reply_markup=markup)
