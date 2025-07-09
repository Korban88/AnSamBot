# main.py

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from analysis import analyze_cryptos, load_top3_cache
from crypto_utils import get_current_price
from tracking import track_price

# Активные сигналы из top-3
used_signals = []

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Получить сигнал", callback_data="get_signal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        await send_next_signal(query, context)

    elif query.data.startswith("track_"):
        coin_id = query.data.replace("track_", "")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"⏳ Начинаю отслеживание монеты *{coin_id}*...", parse_mode="Markdown")
        asyncio.create_task(track_price(context.bot, coin_id))

async def send_next_signal(query, context: ContextTypes.DEFAULT_TYPE):
    top3 = load_top3_cache()
    if not top3:
        top3 = analyze_cryptos()

    if not top3:
        await query.message.reply_text("⚠️ Не удалось получить сигнал. Попробуй позже.")
        return

    # Выбираем монету, которая ещё не была показана
    next_coin = None
    for coin in top3:
        if coin["id"] not in used_signals:
            next_coin = coin
            used_signals.append(coin["id"])
            break

    if not next_coin:
        used_signals.clear()
        next_coin = top3[0]
        used_signals.append(next_coin["id"])

    coin = next_coin
    coin_id = coin["id"]
    price = coin["price"]
    target_price = price * 1.05
    stop_loss_price = price * 0.97
    change_24h = coin["change_24h"]
    rsi = coin["rsi"]
    ma = coin["ma"]
    prob = coin["probability"]

    explanation = (
        f"*Сигнал по монете:* `{coin_id}`\n"
        f"🎯 Цель: +5%\n"
        f"💰 Вход: ${price:.4f}\n"
        f"📈 Целевая цена: ${target_price:.4f}\n"
        f"🛑 Стоп-лосс: ${stop_loss_price:.4f}\n"
        f"📊 Вероятность роста: *{prob}%*\n\n"
        f"— RSI: {rsi:.1f} (до 30 — перепроданность)\n"
        f"— MA: ${ma:.4f} (скользящая средняя)\n"
        f"— 24ч изменение: {change_24h:+.2f}%"
    )

    keyboard = [
        [InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{coin_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(explanation, parse_mode="Markdown", reply_markup=reply_markup)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен...")
    app.run_polling()
