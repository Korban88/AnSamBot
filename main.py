import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN
from crypto_utils import fetch_prices
import top3_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Получить цены", callback_data="get_prices")],
        [InlineKeyboardButton("Топ-3 монеты", callback_data="get_top3")]
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
    elif query.data == "get_top3":
        await get_top3(update)

async def get_prices(update: Update) -> None:
    prices = await fetch_prices()
    if not prices:
        await update.callback_query.message.reply_text("⚠️ Не удалось получить данные о ценах.")
        return

    message = "*Актуальные цены монет:*\n"
    for coin_id, price in prices.items():
        # MarkdownV2 требует экранирования точек и прочего
        coin_name = coin_id.replace("_", "\\_").capitalize()
        message += f"{coin_name}: ${price}\n"

    await update.callback_query.message.reply_text(message, parse_mode="MarkdownV2")

async def get_top3(update: Update) -> None:
    top3 = top3_cache.get_top3()
    if not top3:
        await update.callback_query.message.reply_text("⚠️ Топ-3 монеты пока не сохранены.")
        return

    message = "*Топ-3 монеты:*\n"
    for coin in top3:
        coin_name = coin.replace("_", "\\_")
        message += f"{coin_name}\n"
    await update.callback_query.message.reply_text(message, parse_mode="MarkdownV2")

async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(get_prices|get_top3)$"))

    logger.info("🚀 Бот запущен")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
