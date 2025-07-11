import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from analysis import analyze_cryptos
from config import TELEGRAM_BOT_TOKEN, OWNER_ID, TARGET_PROFIT_PERCENT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.effective_chat:
        await update.effective_chat.send_message(
            "Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "get_signal":
        await send_signal(update, context)

async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    coins = analyze_cryptos()
    if not coins:
        await update.effective_chat.send_message("⚠️ Нет подходящих монет для сигнала.")
        return
    coin = coins[0]
    stop_loss_price = round(coin["price"] * (1 - 0.03), 4)
    message = (
        f"*🟢 Сигнал на рост: {coin['id'].capitalize()}*\n"
        f"Цена входа: {coin['price']}\n"
        f"Цель: +{TARGET_PROFIT_PERCENT}%\n"
        f"Стоп-лосс: {stop_loss_price}\n"
        f"Вероятность роста: {coin['growth_probability']}%"
    )
    keyboard = [[InlineKeyboardButton("Следить за монетой", callback_data=f"track_{coin['id']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_chat.send_message(message, reply_markup=reply_markup, parse_mode="Markdown")

async def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("🚀 Бот запущен")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
