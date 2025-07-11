import asyncio
import logging
import json
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from crypto_utils import fetch_and_cache_indicators, load_indicators
from analysis import analyze_cryptos
from config import TELEGRAM_BOT_TOKEN, OWNER_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("У вас нет доступа к боту.")
        return
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!")
    await send_signal(update, context)

async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top3 = analyze_cryptos()
    if not top3:
        await update.message.reply_text("⚠️ Нет подходящих монет для сигнала.")
        return
    coin = top3[0]
    if "id" in coin:
        keyboard = [[InlineKeyboardButton("Следить за монетой", callback_data=coin['id'])]]
        await update.message.reply_text(
            f"Монета: {coin['id']}\nЦена: {coin['price']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("⚠️ Нет подходящих монет для сигнала.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(f"Начинаю отслеживать: {query.data}")

async def cron_updater():
    while True:
        try:
            fetch_and_cache_indicators()
        except Exception as e:
            logger.error(f"Ошибка в cron_updater: {e}")
        await asyncio.sleep(1800)  # 30 минут

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    asyncio.create_task(cron_updater())

    logger.info("🚀 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
