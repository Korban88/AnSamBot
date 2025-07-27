import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from analysis import analyze_cryptos
from config import OWNER_ID

SIGNAL_CACHE_FILE = "top_signals_cache.json"
USED_SYMBOLS_FILE = "used_symbols.json"
SIGNAL_TRACKER_FILE = "signal_tracker.json"


def reset_cache():
    for file in [SIGNAL_CACHE_FILE, USED_SYMBOLS_FILE, SIGNAL_TRACKER_FILE]:
        if os.path.exists(file):
            os.remove(file)


def load_used_symbols():
    if os.path.exists(USED_SYMBOLS_FILE):
        with open(USED_SYMBOLS_FILE, "r") as f:
            return json.load(f)
    return []


def save_used_symbol(symbol):
    used = load_used_symbols()
    used.append(symbol)
    with open(USED_SYMBOLS_FILE, "w") as f:
        json.dump(used[-6:], f)  # храним только последние 6


def load_signal_cache():
    if os.path.exists(SIGNAL_CACHE_FILE):
        with open(SIGNAL_CACHE_FILE, "r") as f:
            return json.load(f)
    return []


def save_signal_cache(signals):
    with open(SIGNAL_CACHE_FILE, "w") as f:
        json.dump(signals, f)


def get_next_signal():
    signals = load_signal_cache()
    if not signals:
        return None

    index = 0
    if os.path.exists(SIGNAL_TRACKER_FILE):
        with open(SIGNAL_TRACKER_FILE, "r") as f:
            index = json.load(f).get("index", 0)

    if index >= len(signals):
        return None

    next_signal = signals[index]

    with open(SIGNAL_TRACKER_FILE, "w") as f:
        json.dump({"index": index + 1}, f)

    return next_signal


async def send_signal_message(user_id, context):
    signal = get_next_signal()

    if not signal:
        await context.bot.send_message(chat_id=user_id, text="Нет подходящих сигналов.")
        return

    symbol = signal.get("symbol", "?").upper()
    price = float(str(signal.get("current_price", 0)).replace("$", ""))
    target = round(price * 1.05, 4)
    stop_loss = round(price * 0.97, 4)
    change = signal.get("price_change_percentage_24h", 0)
    prob = signal.get("probability", 0)

    text = (
        f"📈 *Сигнал по монете {symbol}*\n"
        f"Текущая цена: ${price}\n"
        f"Цель: ${target} (+5%)\n"
        f"Стоп-лосс: ${stop_loss} (-3%)\n"
        f"Изменение за 24ч: {change}%\n"
        f"Вероятность роста: *{prob}%*"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track:{symbol}")]
    ])

    await context.bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )


async def send_analysis_log(user_id, context):
    from analysis import ANALYSIS_LOG

    if not ANALYSIS_LOG:
        await context.bot.send_message(chat_id=user_id, text="Лог анализа пока пуст.")
        return

    log_text = "\n".join(ANALYSIS_LOG)
    await context.bot.send_message(chat_id=user_id, text=f"*Анализ монет:*

{log_text}", parse_mode=ParseMode.MARKDOWN)
