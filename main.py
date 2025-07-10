import os
import json
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from analysis import analyze_cryptos
from tracking import start_tracking_coin, stop_all_tracking
from config import TELEGRAM_BOT_TOKEN as TELEGRAM_TOKEN, OWNER_ID

# Экранирование MarkdownV2
def escape_markdown_v2(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in escape_chars else c for c in str(text))

# Кнопка Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Получить ещё сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")]
    ]
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Генерация сигнала
async def get_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coins = analyze_cryptos()

    if not coins or coins[0]["id"] == "diagnostics":
        await update.callback_query.message.reply_text("Нет подходящих монет для сигнала.")
        return

    coin = coins[0]
    price = round(coin["price"], 4)
    target_price = round(price * 1.05, 4)
    stop_loss = round(price * 0.97, 4)

    keyboard = [
        [InlineKeyboardButton("Следить за монетой", callback_data=f"track:{coin['id']}")]
    ]

    message = (
        f"*🟢 Сигнал на рост: {escape_markdown_v2(coin['id'].capitalize())}*\n"
        f"Цена: {escape_markdown_v2(price)}\n"
        f"24ч: {escape_markdown_v2(coin['change_24h'])}%\n"
        f"RSI: {escape_markdown_v2(coin['rsi'])} \\| MA: {escape_markdown_v2(coin['ma'])}\n"
        f"🎯 Цель: {escape_markdown_v2(target_price)}\n"
        f"🛑 Стоп-лосс: {escape_markdown_v2(stop_loss)}\n"
        f"📈 Вероятность роста: *{escape_markdown_v2(coin['probability'])}%*"
    )

    await update.callback_query.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        await get_signal(update, context)
    elif query.data == "stop_tracking":
        await stop_all_tracking(context)
        await query.message.reply_text("⛔ Все отслеживания остановлены.")
    elif query.data.startswith("track:"):
        coin_id = query.data.split(":")[1]
        await start_tracking_coin(coin_id, context, OWNER_ID)
        await query.message.reply_text(f"📡 Начато отслеживание {coin_id}")

# Запуск бота
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🚀 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
