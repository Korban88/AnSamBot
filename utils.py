import json
import os
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.background import BackgroundScheduler
from analysis import analyze_cryptos
from telegram.ext import Application
from config import OWNER_ID

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


def load_signal_cache():
    if os.path.exists(SIGNAL_CACHE_FILE):
        with open(SIGNAL_CACHE_FILE, "r") as f:
            return json.load(f)
    return []


def save_signal_cache(signals):
    with open(SIGNAL_CACHE_FILE, "w") as f:
        json.dump(signals, f)


def schedule_daily_signal_check(app: Application, user_id: int):
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    loop = asyncio.get_event_loop()
    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(send_daily_signal(user_id, app), loop),
        "cron", hour=8, minute=0
    )
    scheduler.start()


async def send_signal_message(user_id, context):
    signal_cache = load_signal_cache()
    used_symbols = load_used_symbols()
    signal_to_send = None

    for signal in signal_cache:
        if signal['symbol'] not in used_symbols:
            signal_to_send = signal
            break

    if not signal_to_send:
        await context.bot.send_message(chat_id=user_id, text="Нет подходящих сигналов на данный момент.")
        return

    symbol = signal_to_send['symbol']
    price = float(signal_to_send.get("current_price", 0))
    target_price = round(price * 1.05, 4)
    stop_loss = round(price * 0.97, 4)
    probability = signal_to_send.get("probability", "-")
    change_24h = signal_to_send.get("price_change_percentage_24h", "-")

    message = (
        f"📈 *Сигнал на рост монеты {symbol.upper()}*\n"
        f"• Цена входа: *${price}*\n"
        f"• Цель: *+5% ➜ ${target_price}*\n"
        f"• Стоп-лосс: *${stop_loss}*\n"
        f"• Изменение за 24ч: *{change_24h}%*\n"
        f"• Вероятность роста: *{probability}%*"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track_{symbol}")]
    ])

    await context.bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown', reply_markup=keyboard)
    save_used_symbol(symbol)


async def send_daily_signal(user_id, app):
    class DummyContext:
        bot = app.bot
    dummy_context = DummyContext()
    await send_signal_message(user_id, dummy_context)


async def debug_analysis_message(user_id, context):
    from analysis import ANALYSIS_LOG
    text = "\n\n".join(ANALYSIS_LOG[-20:])
    if not text:
        text = "Анализ ещё не проводился."
    await context.bot.send_message(chat_id=user_id, text=f"*Анализ монет:*\n{text}", parse_mode='Markdown')


async def debug_cache_message(user_id, context):
    cache = load_signal_cache()
    if not cache:
        await context.bot.send_message(chat_id=user_id, text="Кэш пуст.")
        return
    formatted = [f"{s['symbol'].upper()} — {s['probability']}% — ${s['current_price']}" for s in cache]
    await context.bot.send_message(chat_id=user_id, text=f"*Кэш сигналов:*\n" + "\n".join(formatted), parse_mode='Markdown')


# 🔹 Новая функция для ручного обновления сигналов
async def manual_refresh_signals():
    """
    Принудительно обновляет кэш сигналов.
    """
    signals = await analyze_cryptos()
    save_signal_cache(signals)
    return signals
