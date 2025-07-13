from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from analysis import get_top_signals

logger = logging.getLogger("handlers")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!\nНажмите кнопку ниже, чтобы получить сигнал:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        await get_signal_handler(update, context, from_button=True)

async def get_signal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, from_button=False):
    if from_button:
        message = update.callback_query.message
    else:
        message = update.message

    top_signals = await get_top_signals()

    if not top_signals:
        await message.reply_text("Нет подходящих монет по текущим условиям.")
        return

    signal = top_signals[0]

    text = (
        f"💡 Сигнал по монете: {signal['name']}\n\n"
        f"Цена входа: {signal['entry_price']}\n"
        f"Цель +5%: {signal['target_price']}\n"
        f"Стоп-лосс: {signal['stop_loss']}\n"
        f"Вероятность роста: {signal['probability']}%\n"
    )

    await message.reply_text(text)
