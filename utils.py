import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.background import BackgroundScheduler
from analysis import analyze_cryptos, ANALYSIS_LOG
from telegram.ext import Application
import logging

USED_SYMBOLS_FILE = "used_symbols.json"
SIGNAL_CACHE_FILE = "top_signals_cache.json"

logger = logging.getLogger(__name__)


def reset_cache():
    if os.path.exists(SIGNAL_CACHE_FILE):
        os.remove(SIGNAL_CACHE_FILE)
    if os.path.exists(USED_SYMBOLS_FILE):
        os.remove(USED_SYMBOLS_FILE)


def load_used_symbols():
    if os.path.exists(USED_SYMBOLS_FILE):
        with open(USED_SYMBOLS_FILE, "r") as f:
            return json.load(f)
    return []


def save_used_symbol(symbol):
    used = load_used_symbols()
    used.append(symbol)
    with open(USED_SYMBOLS_FILE, "w") as f:
        json.dump(used, f)


def load_signal_cache():
    if os.path.exists(SIGNAL_CACHE_FILE):
        with open(SIGNAL_CACHE_FILE, "r") as f:
            return json.load(f)
    return []


def save_signal_cache(signals):
    with open(SIGNAL_CACHE_FILE, "w") as f:
        json.dump(signals, f)


async def refresh_signal_cache():
    top_signals = await analyze_cryptos()
    save_signal_cache(top_signals)
    logger.info("♻️ Кэш сигналов обновлён.")


def schedule_daily_signal_check(app: Application):
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        lambda: app.create_task(refresh_signal_cache()),
        trigger="cron",
        hour=8,
        minute=0,
        id="daily_signal_check"
    )
    scheduler.start()


async def send_signal_message(user_id, context):
    signals = load_signal_cache()
    used = load_used_symbols()

    for signal in signals:
        if signal["symbol"] in used:
            continue

        save_used_symbol(signal["symbol"])

        price_str = str(signal["current_price"]).replace("$", "").replace(",", "")
        try:
            price = float(price_str)
        except ValueError:
            price = 0.0

        target_price = round(price * 1.05, 4)
        stop_loss = round(price * 0.97, 4)

        msg = (
            f"*💰 Сигнал на покупку: {signal['symbol'].upper()}*\n"
            f"Текущая цена: ${price}\n"
            f"Цель +5%: ${target_price}\n"
            f"Стоп-лосс: ${stop_loss}\n"
            f"Изменение за 24ч: {signal['price_change_percentage_24h']}%\n"
            f"Вероятность роста: *{signal['probability']}%*"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track:{signal['id']}")]
        ])

        await context.bot.send_message(chat_id=user_id, text=msg, reply_markup=keyboard, parse_mode="Markdown")

        return

    await context.bot.send_message(chat_id=user_id, text="⚠️ Нет подходящих сигналов.")


async def send_signal_cache(user_id, context):
    signals = load_signal_cache()
    if not signals:
        await context.bot.send_message(chat_id=user_id, text="⚠️ Кэш сигналов пуст.")
        return

    text = "*Кэш сигналов:*\n"
    for s in signals:
        text += f"— {s['symbol'].upper()} | Цена: ${s['current_price']} | +24ч: {s['price_change_percentage_24h']}% | Вероятность: {s['probability']}%\n"

    await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")


async def send_analysis_log(user_id, context):
    if not ANALYSIS_LOG:
        await context.bot.send_message(chat_id=user_id, text="Лог анализа пуст.")
        return

    log_text = "\n".join(ANALYSIS_LOG)
    await context.bot.send_message(chat_id=user_id, text=f"*Анализ монет:*\n{log_text}", parse_mode="MarkdownV2")
