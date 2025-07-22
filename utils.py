import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.background import BackgroundScheduler
from analysis import analyze_cryptos
from config import TELEGRAM_BOT_TOKEN
from telegram.ext import Application

USED_SYMBOLS_FILE = "used_symbols.json"
SIGNAL_CACHE_FILE = "top_signals_cache.json"

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
        json.dump(used[-6:], f)

def get_next_top_signal():
    if not os.path.exists(SIGNAL_CACHE_FILE):
        return None

    with open(SIGNAL_CACHE_FILE, "r") as f:
        signals = json.load(f)

    used = load_used_symbols()

    for signal in signals:
        if signal["symbol"] not in used:
            save_used_symbol(signal["symbol"])
            return signal
    return None

async def cache_top_signals():
    top_signals = await analyze_cryptos()
    with open(SIGNAL_CACHE_FILE, "w") as f:
        json.dump(top_signals, f)

async def send_signal_message(app: Application):
    await cache_top_signals()
    signal = get_next_top_signal()

    if signal:
        message = (
            f"*🚀 Сигнал на покупку: {signal['symbol']}*\n\n"
            f"*Цена входа:* ${signal['current_price']}\n"
            f"*Цель:* +5%\n"
            f"*Стоп-лосс:* -3%\n"
            f"*Изменение за 24ч:* {signal['price_change_percentage_24h']}%\n"
            f"*Вероятность роста:* {signal['probability']}%\n"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track_{signal['symbol']}")]
        ])

        from config import OWNER_ID
        await app.bot.send_message(chat_id=OWNER_ID, text=message, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await app.bot.send_message(chat_id=OWNER_ID, text="Нет подходящих сигналов на текущий момент.")

def schedule_daily_signal_check(app, owner_id):
    """
    Запускает планировщик отправки сигнала каждый день в 8:00 по МСК
    """
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    scheduler.add_job(lambda: app.create_task(send_signal_message(app)),
                      trigger='cron', hour=8, minute=0, id='daily_signal')
    scheduler.start()
