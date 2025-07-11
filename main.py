import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from analysis import analyze_cryptos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("Получить сигнал", callback_data="get_signal")]]
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        coin = analyze_cryptos()
        if coin:
            message = (
                f"*🟢 Сигнал на рост: {coin['id'].capitalize()}*
"
                f"Текущая цена: {coin['price']} USD\n"
                f"Цель: +{coin['target_percent']}%\n"
                f"RSI: {coin['rsi']} | MA: {coin['ma']}\n"
                f"Изменение за 24ч: {coin['change_24h']}%"
            )
            keyboard = [[InlineKeyboardButton("Следить", callback_data=f"track_{coin['id']}")]]
            await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="MarkdownV2")
        else:
            await query.message.reply_text("⚠️ Нет подходящих монет для сигнала.")

async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
