from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from analysis import analyze_cryptos, get_next_signal_from_cache
from crypto_list import CRYPTO_LIST

from tracking import start_tracking, stop_all_trackings
import asyncio


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен.")


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Нажмите кнопку, чтобы получить сигнал.")


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        # Если кеш пуст — сгенерировать новый
        top_signals = await analyze_cryptos(CRYPTO_LIST)
        signal = get_next_signal_from_cache()

        if not signal:
            await query.edit_message_text("Не удалось получить сигнал.")
            return

        text = (
            f"*Монета:* {signal['coin'].capitalize()}\n"
            f"*Цена входа:* {signal['price']}\n"
            f"*Цель:* {round(signal['price'] * 1.05, 4)} (+5%)\n"
            f"*Стоп-лосс:* {round(signal['price'] * 0.97, 4)}\n"
            f"*Текущая цена:* {signal['price']}\n"
            f"*Изменение за 24 часа:* {signal['change_24h']}%\n"
            f"*Вероятность роста:* {signal['probability']}%"
        )

        keyboard = [
            [InlineKeyboardButton("Следить за монетой", callback_data=f"track_{signal['coin']}")]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

    elif query.data.startswith("track_"):
        coin = query.data.split("_")[1]
        asyncio.create_task(start_tracking(coin, query.message.chat_id))
        await query.edit_message_text(f"Начато отслеживание монеты: {coin.upper()}")

    elif query.data == "stop_tracking":
        stop_all_trackings()
        await query.edit_message_text("Все отслеживания остановлены.")

    elif query.data == "reset_cache":
        from os import remove
        try:
            remove("top_signals_cache.json")
            await query.edit_message_text("Кеш сигналов сброшен.")
        except FileNotFoundError:
            await query.edit_message_text("Кеш уже пуст.")
