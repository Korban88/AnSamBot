# main.py — адаптирован под Railway, без конфликтов asyncio

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from analysis import analyze_cryptos
from tracking import start_tracking_coin, stop_all_tracking

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!")
    await send_signal(update, context)

# Кнопка
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("track_"):
        coin_id = query.data.split("_")[1]
        await start_tracking_coin(coin_id, context)
        await query.edit_message_text(f"🔔 Теперь отслеживаем {coin_id}")
    elif query.data == "stop_all":
        await stop_all_tracking(context)
        await query.edit_message_text("⛔️ Все отслеживания остановлены")

# Сигнал
async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = analyze_cryptos()
    if not result:
        await update.message.reply_text("⚠️ Нет подходящих монет для сигнала.")
        return

    coin = result[0]
    text = (
        f"*🟢 Сигнал на рост: {coin['id'].capitalize()}*
"
        f"Текущая цена: {coin['price']}\n"
        f"Вероятность роста: {coin['probability']}%\n"
    )

    keyboard = [
        [InlineKeyboardButton(f"Следить за {coin['id']}", callback_data=f"track_{coin['id']}")],
        [InlineKeyboardButton("Остановить все", callback_data="stop_all")]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Основной запуск
async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
