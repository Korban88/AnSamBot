# main.py (с диагностикой)

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from analysis import analyze_cryptos, load_top3_cache
from crypto_utils import get_current_price
from tracking import track_price
from crypto_list import TELEGRAM_WALLET_CRYPTOS
from crypto_utils import get_24h_change, get_rsi, get_ma

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
        await send_diagnostic_report(query, context)

    elif query.data.startswith("track_"):
        coin_id = query.data.replace("track_", "")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"⏳ Начинаю отслеживание монеты *{coin_id}*...", parse_mode="Markdown")
        asyncio.create_task(track_price(context.bot, coin_id))

async def send_diagnostic_report(query, context: ContextTypes.DEFAULT_TYPE):
    text = "*🔍 Диагностика анализа монет:*\n"
    ok = False

    for coin_id in TELEGRAM_WALLET_CRYPTOS[:10]:  # первые 10 монет для теста
        try:
            price = get_current_price(coin_id)
            change_24h = get_24h_change(coin_id)
            rsi = get_rsi(coin_id)
            ma = get_ma(coin_id)

            if None in (price, change_24h, rsi, ma):
                text += f"⛔ `{coin_id}` — недоступны данные\n"
                continue

            score = 0
            if rsi < 30:
                score += 30
            elif rsi < 40:
                score += 20
            elif rsi < 50:
                score += 10

            if price > ma:
                score += 25
            if change_24h > 0:
                score += 15
            elif -1 <= change_24h <= 0:
                score += 5

            if price > 1:
                score += min(price ** 0.2, 10)

            prob = min(90.0, max(30.0, score))

            text += (
                f"\n✅ `{coin_id}`\n"
                f"Цена: ${price:.4f}\n"
                f"24ч: {change_24h:+.2f}%\n"
                f"RSI: {rsi:.1f} | MA: {ma:.4f}\n"
                f"Score: {score:.1f} | Вероятность: {prob:.1f}%\n"
            )
            ok = True
        except Exception as e:
            text += f"💥 `{coin_id}` — ошибка: {e}\n"

    await query.message.reply_text(text, parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен...")
    app.run_polling()
