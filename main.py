import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from tracking import start_tracking_coin, stop_all_tracking
from analysis import analyze_cryptos
from crypto_utils import fetch_and_cache_indicators

# ВРЕМЕННЫЙ ЗАПУСК ЗАПОЛНЕНИЯ КЭША
fetch_and_cache_indicators()
exit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_all")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔️ У вас нет доступа к этому боту.")
        return
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=build_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.callback_query.answer("⛔️ Нет доступа", show_alert=True)
        return

    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        signal = analyze_cryptos()
        await query.edit_message_text(signal, reply_markup=build_keyboard(), parse_mode="MarkdownV2")

    elif query.data == "stop_all":
        stop_all_tracking()
        await query.edit_message_text("🛑 Все отслеживания остановлены.", reply_markup=build_keyboard())


async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("🚀 Бот запущен")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
