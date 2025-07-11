import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from analysis import analyze_cryptos, load_top3_cache, save_top3_cache
from crypto_utils import fetch_and_cache_indicators
from tracking import start_tracking_coin, stop_all_trackings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция генерации сигнала по top-3
async def generate_signal(update: Update = None, context: ContextTypes.DEFAULT_TYPE = None):
    top3 = load_top3_cache()
    if not top3:
        cryptos = await analyze_cryptos()
        top3 = cryptos[:3]
        save_top3_cache(top3)
        logger.info("Top-3 монеты обновлены и сохранены")

    if update:
        if top3:
            coin = top3.pop(0)
            save_top3_cache(top3)
            keyboard = [[InlineKeyboardButton(f"Следить за {coin['id'].capitalize()}", callback_data=f"track_{coin['id']}")]]
            message = (
                f"*🟢 Сигнал на рост: {coin['id'].capitalize()}*
"
                f"Цена: {coin['price']}$\nВероятность роста: {coin['probability']}%\n"
                f"Цель: {coin['target_price']}$ | Стоп-лосс: {coin['stop_loss']}$"
            )
            await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="MarkdownV2")
        else:
            await update.message.reply_text("⚠️ Нет подходящих монет для сигнала.")

# Хендлеры команд и кнопок
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    keyboard = [[InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
                [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_all")]]
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "get_signal":
        await generate_signal(update, context)
    elif query.data.startswith("track_"):
        coin_id = query.data.split("_")[1]
        await start_tracking_coin(coin_id, context.bot)
        await query.message.reply_text(f"🔔 Отслеживание {coin_id.capitalize()} запущено.")
    elif query.data == "stop_all":
        stop_all_trackings()
        await query.message.reply_text("⛔ Все отслеживания остановлены.")

async def main():
    fetch_and_cache_indicators()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    loop = asyncio.get_event_loop()
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    try:
        await asyncio.Event().wait()
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            logger.warning("Запущен в окружении с уже активным event loop. Пропускаем asyncio.run().")
        else:
            raise
