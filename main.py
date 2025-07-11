import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

import config
from analysis import analyze_cryptos
from tracking import start_tracking_coin, stop_all_tracking
from crypto_utils import fetch_and_cache_indicators

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Получить сигнал", callback_data='get_signal')],
        [InlineKeyboardButton("Остановить все отслеживания", callback_data='stop_tracking')]
    ]
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'get_signal':
        await send_signal(update, context)
    elif query.data == 'stop_tracking':
        stop_all_tracking()
        await query.edit_message_text("✅ Отслеживание монет остановлено.")

async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_coins = analyze_cryptos()

    if not top_coins:
        await update.callback_query.message.reply_text("⚠️ Нет подходящих монет для сигнала.")
        return

    coin = top_coins[0]
    message = (
        f"*🟢 Сигнал на рост: {coin['id'].capitalize()}*\n"
        f"Текущая цена: {coin['price']} USD\n"
        f"Цель: +{config.TARGET_PROFIT_PERCENT}%\n"
        f"Стоп-лосс: {coin['price'] * 0.97:.2f} USD\n"
    )

    keyboard = [[InlineKeyboardButton("Следить за монетой", callback_data=f"track_{coin['id']}")]]

    await update.callback_query.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

async def main():
    fetch_and_cache_indicators()

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
