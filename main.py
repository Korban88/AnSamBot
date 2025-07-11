import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from crypto_utils import fetch_and_cache_indicators, get_current_price, get_24h_change, get_rsi, get_ma
from crypto_list import TELEGRAM_WALLET_CRYPTOS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("⛔ Остановить все отслеживания", callback_data="stop_all")]
    ]
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "get_signal":
        await query.message.reply_text("⚠️ Нет подходящих монет для сигнала.")
    if query.data == "stop_all":
        await query.message.reply_text("⛔ Отслеживания остановлены.")

async def main():
    print("📥 Обновляем indicators_cache.json...")
    fetch_and_cache_indicators()
    print("✅ Готово!")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
