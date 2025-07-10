import logging
import time
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN as TELEGRAM_TOKEN, OWNER_ID
from analysis import analyze_cryptos, load_top3_cache
from tracking import start_tracking_coin, stop_all_tracking
from crypto_utils import fetch_and_cache_indicators

logging.basicConfig(level=logging.INFO)
user_signal_index = {}

def escape_markdown(text):
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in escape_chars else c for c in str(text))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📊 Получить сигнал", callback_data="get_signal")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup)

async def get_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_signal_index:
        user_signal_index[user_id] = 0

    top_3 = load_top3_cache()
    if not top_3:
        top_3 = analyze_cryptos()

    if not top_3:
        await update.callback_query.message.reply_text("🚫 Нет доступных сигналов. Попробуйте позже.")
        return

    index = user_signal_index[user_id] % len(top_3)
    coin = top_3[index]
    user_signal_index[user_id] += 1

    price = coin["price"]
    target_price = round(price * 1.05, 4)
    stop_loss = round(price * 0.97, 4)
    message = (
        f"*🟢 Сигнал на рост: {escape_markdown(coin['id'].capitalize())}*\n"
        f"Цена: {escape_markdown(str(price))}\n"
        f"24ч: {escape_markdown(str(coin['change_24h']))}%\n"
        f"RSI: {escape_markdown(str(coin['rsi']))} | MA: {escape_markdown(str(coin['ma']))}\n"
        f"🎯 Цель: {escape_markdown(str(target_price))}\n"
        f"🛑 Стоп-лосс: {escape_markdown(str(stop_loss))}\n"
        f"📈 Вероятность роста: *{escape_markdown(str(coin['probability']))}%*"
    )

    keyboard = [[InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track_{coin['id']}")]]
    await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="MarkdownV2")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("track_"):
        coin_id = query.data.split("_", 1)[1]
        await start_tracking_coin(coin_id, query.message.chat_id, context.bot)

    elif query.data == "get_signal":
        await get_signal(update, context)

async def stop_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop_all_tracking(update.effective_chat.id, context.bot)
    await update.message.reply_text("⛔ Все отслеживания остановлены.")

def main():
    fetch_and_cache_indicators()  # Загрузка индикаторов в кеш

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop_tracking))
    app.add_handler(CallbackQueryHandler(button_handler))
    logging.info("🚀 Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
