from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from utils import (
    send_signal_message,
    reset_cache,
    debug_cache_message,
    debug_analysis_message,
    manual_refresh_signals
)
from tracking import CoinTracker
from crypto_utils import get_current_price
import json
import os
import pytz
from datetime import datetime

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

reply_keyboard = [
    [KeyboardButton("📈 Получить сигнал")],
    [KeyboardButton("🔁 Обновить сигналы"), KeyboardButton("🔁 Сбросить кеш")],
    [KeyboardButton("⛔ Остановить все отслеживания")],
    [KeyboardButton("📦 Кеш сигналов"), KeyboardButton("📊 Анализ монет")]
]
reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=reply_markup
    )

start_handler = CommandHandler("start", start)


async def analyze_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await manual_refresh_signals(update.effective_user.id, context)

analyze_command_handler = CommandHandler("analyze", analyze_handler)

debug_handler = CommandHandler("debug_cache", lambda update, context: debug_cache_message(update.effective_user.id, context))
debug_analysis_handler = CommandHandler("debug_analysis", lambda update, context: debug_analysis_message(update.effective_user.id, context))


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith("track_"):
        symbol = query.data.split("_", 1)[1]
        CoinTracker.track(user_id, symbol, context)
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ Монета {symbol.upper()} добавлена в отслеживание.\n"
                 f"Вечером вы получите отчёт о её динамике."
        )

button_handler = CallbackQueryHandler(button_callback)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_id = update.effective_user.id

    if "обновить" in text:
        await manual_refresh_signals(user_id, context)
    elif "сигнал" in text and "кеш" not in text:
        await send_signal_message(user_id, context)
    elif "сброс" in text:
        reset_cache()
        await update.message.reply_text("✅ Кеш сброшен.", reply_markup=reply_markup)
    elif "анализ" in text:
        await debug_analysis_message(user_id, context)
    elif "кеш" in text:
        await debug_cache_message(user_id, context)
    elif "стоп" in text or "отмена" in text:
        CoinTracker.clear_all()
        await update.message.reply_text("⛔ Все отслеживания остановлены.", reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            "✉️ Напиши 'сигнал', 'анализ', 'кеш' или 'сброс'.",
            reply_markup=reply_markup
        )


# 🔍 Команда для проверки tracking_data.json
async def show_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CoinTracker.load_tracking_data()
    data = CoinTracker.tracked.get(str(update.effective_user.id), {})
    if not data:
        await update.message.reply_text("⚠️ Нет активных отслеживаний.")
        return

    report_lines = ["📂 Текущие отслеживания:"]
    for symbol, details in data.items():
        initial = details.get("initial_price")
        coin_id = details.get("coin_id")
        if not initial or initial == "fetch_error":
            current = await get_current_price(coin_id)
            if current:
                details["initial_price"] = current
                CoinTracker.save_tracking_data()
                initial = current

        # конвертация времени в МСК
        try:
            utc_time = datetime.fromisoformat(details.get("start_time"))
            local_time = utc_time.astimezone(MOSCOW_TZ).strftime("%d.%m %H:%M")
        except Exception:
            local_time = details.get("start_time")

        report_lines.append(
            f"{symbol.upper()} | Цена входа: {initial} | Время: {local_time}"
        )

    await update.message.reply_text("\n".join(report_lines))

show_tracking_handler = CommandHandler("show_tracking", show_tracking)
