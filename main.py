import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.helpers import escape_markdown

from config import TELEGRAM_BOT_TOKEN
from crypto_utils import fetch_prices
import top3_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

latest_prices = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Получить цены", callback_data="get_prices")],
        [InlineKeyboardButton("Топ-3 монеты", callback_data="get_top3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(
            escape_markdown("Добро пожаловать в новую жизнь, Корбан!"), reply_markup=reply_markup, parse_mode="MarkdownV2"
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        if query.data == "get_prices":
            await get_prices(update)
        elif query.data == "get_top3":
            await get_top3(update)
    except Exception as e:
        logger.error(f"Ошибка при обработке кнопки: {e}")
        await query.message.reply_text("⚠️ Произошла ошибка. Попробуйте снова.")

async def get_prices(update: Update) -> None:
    global latest_prices
    latest_prices = await fetch_prices()
    if not latest_prices:
        await update.callback_query.message.reply_text(escape_markdown("⚠️ Не удалось получить данные о ценах."), parse_mode="MarkdownV2")
        return

    message = "*Актуальные цены монет:*\n"
    for coin_id, price in latest_prices.items():
        line = f"{coin_id.capitalize()}: {price if price != 'нет данных' else 'нет данных'}$\n"
        message += escape_markdown(line)

    await update.callback_query.message.reply_text(message, parse_mode="MarkdownV2")

async def get_top3(update: Update) -> None:
    top3 = top3_cache.get_top3()
    if not top3:
        await update.callback_query.message.reply_text(escape_markdown("⚠️ Топ-3 монеты пока не сохранены."), parse_mode="MarkdownV2")
        return

    message = "*Топ-3 монеты:*\n"
    for coin in top3:
        message += escape_markdown(f"{coin}\n")

    await update.callback_query.message.reply_text(message, parse_mode="MarkdownV2")

async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Бот запущен")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
