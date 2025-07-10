import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from analysis import analyze_cryptos
from tracking import start_tracking_coin, stop_all_tracking

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_signal_index = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        user_id = query.from_user.id
        result = analyze_cryptos()

        if not result:
            await query.message.reply_text("⚠️ Нет подходящих монет для сигнала.")
            return

        index = user_signal_index.get(user_id, 0)
        if index >= len(result):
            index = 0
        coin = result[index]
        user_signal_index[user_id] = index + 1

        message = (
            f"📊 Сигнал: {coin['name'].capitalize()}\n"
            f"Цена: ${coin['price']}\n"
            f"Цель: +5% → ${coin['target_price']}\n"
            f"Стоп-лосс: ${coin['stop_loss']}\n"
            f"Изменение за 24ч: {coin['change_24h']}%\n"
            f"RSI: {coin['rsi']}, MA: {coin['ma']}\n"
            f"Вероятность роста: {coin['growth_probability']}%"
        )
        keyboard = [[InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{coin['id']}")]]
        await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "stop_tracking":
        stop_all_tracking()
        await query.message.reply_text("⛔️ Отслеживание всех монет остановлено.")

    elif query.data.startswith("track_"):
        coin_id = query.data.split("_", 1)[1]
        await query.message.reply_text(f"👁 Отслеживание {coin_id} запущено.")
        await start_tracking_coin(coin_id, context.bot)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))

    logger.info("🚀 Бот запущен")

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
