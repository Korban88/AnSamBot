import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from analysis import analyze_cryptos
from tracking import start_tracking_coin, stop_all_trackings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(
            "Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "get_signal":
        await get_signal(update, context)
    elif query.data == "stop_tracking":
        stop_all_trackings()
        await query.message.reply_text("Все отслеживания остановлены.")

async def get_signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    top_coins = analyze_cryptos()
    if not top_coins:
        await update.callback_query.message.reply_text("⚠️ Нет подходящих монет для сигнала.")
        return
    coin = top_coins[0]
    keyboard = [[InlineKeyboardButton("Следить за монетой", callback_data=f"track_{coin['id']}")]]
    message = (
        f"*🟢 Сигнал на рост: {coin['id'].capitalize()}*\n"
        f"Текущая цена: {coin['price']}\n"
        f"24ч изменение: {coin['change_24h']}%\n"
        f"Вероятность роста: {coin['growth_probability']}%\n"
        f"Цель: +{coin['target_percent']}%\n"
        f"Стоп-лосс: {coin['stop_loss_percent']}%"
    )
    await update.callback_query.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

async def track_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data.startswith("track_"):
        coin_id = query.data.split("_")[1]
        start_tracking_coin(coin_id, context.bot)
        await query.message.reply_text(f"Отслеживание {coin_id} запущено.")

async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(get_signal|stop_tracking)$"))
    app.add_handler(CallbackQueryHandler(track_button_handler, pattern="^track_"))

    logger.info("🚀 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
