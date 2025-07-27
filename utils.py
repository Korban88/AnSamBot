import json
import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Application
from analysis import analyze_cryptos, ANALYSIS_LOG
from config import OWNER_ID

USED_SYMBOLS_FILE = "used_symbols.json"
SIGNAL_CACHE_FILE = "top_signals_cache.json"

# Сброс кеша сигналов и использованных монет
def reset_cache():
    if os.path.exists(SIGNAL_CACHE_FILE):
        os.remove(SIGNAL_CACHE_FILE)
    if os.path.exists(USED_SYMBOLS_FILE):
        os.remove(USED_SYMBOLS_FILE)

# Загрузка использованных символов
def load_used_symbols():
    if os.path.exists(USED_SYMBOLS_FILE):
        with open(USED_SYMBOLS_FILE, "r") as f:
            return json.load(f)
    return []

# Сохранение нового использованного символа
def save_used_symbol(symbol):
    used = load_used_symbols()
    if symbol not in used:
        used.append(symbol)
        with open(USED_SYMBOLS_FILE, "w") as f:
            json.dump(used, f)

# Загрузка кэша топ сигналов
def load_signal_cache():
    if os.path.exists(SIGNAL_CACHE_FILE):
        with open(SIGNAL_CACHE_FILE, "r") as f:
            return json.load(f)
    return []

# Сохранение кэша топ сигналов
def save_signal_cache(signals):
    with open(SIGNAL_CACHE_FILE, "w") as f:
        json.dump(signals, f)

# Планировщик ежедневного сигнала
scheduler = BackgroundScheduler()

def schedule_daily_signal_check(app: Application):
    from utils import handle_scheduled_signal
    scheduler.add_job(lambda: app.create_task(handle_scheduled_signal(app)), trigger='cron', hour=8, minute=0, timezone='Europe/Moscow')
    scheduler.start()

# Отправка одного сигнала пользователю
async def send_signal_message(user_id, context):
    signals = load_signal_cache()
    used = load_used_symbols()

    signal = None
    for s in signals:
        if s["symbol"] not in used:
            signal = s
            break

    if not signal:
        await context.bot.send_message(chat_id=user_id, text="⚠️ Нет подходящих сигналов. Попробуйте позже.")
        return

    save_used_symbol(signal["symbol"])

    price = float(str(signal.get("current_price", 0)).replace("$", ""))
    target = round(price * 1.05, 4)
    stop = round(price * 0.97, 4)
    change = signal.get("price_change_percentage_24h", 0)
    probability = signal.get("probability", 0)

    message = (
        f"📈 *Сигнал на рост монеты {signal['symbol'].upper()}*
"
        f"Цена входа: ${price}\n"
        f"Цель +5%: ${target}\n"
        f"Стоп-лосс: ${stop}\n"
        f"Вероятность роста: {probability}%\n"
        f"Изменение за 24ч: {change}%"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track_{signal['symbol']}")]
    ])

    await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown", reply_markup=keyboard)

# Отправка кэша сигналов в виде отладочного сообщения
async def debug_cache_message(update, context):
    user_id = update.effective_chat.id
    signals = load_signal_cache()
    if not signals:
        await context.bot.send_message(chat_id=user_id, text="⚠️ Кэш сигналов пуст.")
        return

    text = "*Кэш сигналов:*\n"
    for s in signals:
        symbol = s.get("symbol", "?").upper()
        prob = s.get("probability", "?")
        price = s.get("current_price", "?")
        change = s.get("price_change_percentage_24h", "?")
        text += f"{symbol} — ${price}, Δ24ч: {change}%, вероятность: {prob}%\n"

    await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")

# Отправка анализа (лога)
async def send_analysis_log(update, context):
    user_id = update.effective_chat.id
    if ANALYSIS_LOG:
        text = "*Анализ монет:*\n" + "\n".join(ANALYSIS_LOG)
    else:
        text = "⚠️ Анализ ещё не проводился."
    await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
