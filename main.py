import asyncio
import logging
import json
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN
from crypto_utils import fetch_prices

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

latest_prices = {}

CACHE_FILE = "top3_cache.json"

def save_top3(coins: list) -> None:
    Path(CACHE_FILE).write_text(json.dumps(coins, ensure_ascii=False))

def load_top3() -> list:
    if Path(CACHE_FILE).exists():
        return json.loads(Path(CACHE_FILE).read_text())
    return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Получить цены", callback_data="get_prices")],
        [InlineKeyboardButton("Топ-3 монеты", callback_data="top3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(
            "Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "get_prices":
        await get_prices(update)
    elif query.data == "top3":
        await send_top3(update)

async def get_prices(update: Update) -> None:
    global latest_prices
    latest_prices = await fetch_prices()
    if not latest_prices:
        await update.callback_query.message.reply_text("⚠️ Не удалось получить данные о ценах.")
        return

    message = "*Актуальные цены монет:*\n"
    for coin_id, price in latest_prices.items():
        message += f"{coin_id.capitalize()}: ${price}\n"
    await update.callback_query.message.reply_text(message, parse_mode="MarkdownV2")

async def send_top3(update: Update) -> None:
    top3 = load_top3()
    if not top3:
        await update.callback_query.message.reply_text("Топ-3 монет ещё не сохранён.")
        return

    message = "*Топ-3 монеты с вероятностью роста:*\n"
    for coin in top3:
        message += f"{coin['id'].capitalize()} — {coin['probability']}%\n"
    await update.callback_query.message.reply_text(message, parse_mode="MarkdownV2")

async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
