import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.background import BackgroundScheduler
from analysis import analyze_cryptos, ANALYSIS_LOG
from telegram.ext import Application

USED_SYMBOLS_FILE = "used_symbols.json"
SIGNAL_CACHE_FILE = "top_signals_cache.json"
MAX_SIGNAL_CACHE = 6


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
    if symbol not in used:
        used.append(symbol)
    with open(USED_SYMBOLS_FILE, "w") as f:
        json.dump(used[-MAX_SIGNAL_CACHE:], f)


def load_cached_signals():
    if os.path.exists(SIGNAL_CACHE_FILE):
        with open(SIGNAL_CACHE_FILE, "r") as f:
            return json.load(f)
    return []


def get_next_top_signal():
    signals = load_cached_signals()
    used = load_used_symbols()

    for signal in signals:
        if signal["symbol"] not in used:
            save_used_symbol(signal["symbol"])
            return signal
    return None


async def ensure_top_signals_available():
    signals = load_cached_signals()
    used = load_used_symbols()
    unused = [s for s in signals if s["symbol"] not in used]

    # Всегда выполнять анализ (в фоне) для обновления ANALYSIS_LOG
    _ = await analyze_cryptos(run_only_for_log=True)

    if not unused:
        print("⚠️ Кеш пуст или все сигналы использованы — повторный анализ...")
        top_signals = await analyze_cryptos()
        if not top_signals:
            print("⛔ Строгий фильтр не дал результатов — fallback-анализ...")
            top_signals = await analyze_cryptos(fallback=True)
            for s in top_signals:
                s["fallback"] = True
        else:
            for s in top_signals:
                s["fallback"] = False
        with open(SIGNAL_CACHE_FILE, "w") as f:
            json.dump(top_signals[:MAX_SIGNAL_CACHE], f)


async def refresh_signal_cache_job(app: Application):
    signals = load_cached_signals()
    used = load_used_symbols()
    unused = [s for s in signals if s["symbol"] not in used]

    # Всегда выполнять анализ (в фоне) для обновления ANALYSIS_LOG
    _ = await analyze_cryptos(run_only_for_log=True)

    if not unused:
        print("♻️ Автообновление кеша сигналов...")
        top_signals = await analyze_cryptos()
        if not top_signals:
            print("⛔ Fallback-анализ при автообновлении...")
            top_signals = await analyze_cryptos(fallback=True)
            for s in top_signals:
                s["fallback"] = True
        else:
            for s in top_signals:
                s["fallback"] = False
        with open(SIGNAL_CACHE_FILE, "w") as f:
            json.dump(top_signals[:MAX_SIGNAL_CACHE], f)
        print("✅ Кеш сигналов обновлён.")
    else:
        print("🟢 Кеш сигналов актуален — обновление не требуется.")


def fnum(x):
    return f"{x:.2f}".rstrip('0').rstrip('.') if '.' in f"{x:.2f}" else f"{x:.2f}"


async def send_signal_message(user_id, context):
    await ensure_top_signals_available()
    signal = get_next_top_signal()

    if signal:
        price = float(signal.get("current_price", 0))
        target_price = round(price * 1.05, 6)
        stop_price = round(price * 0.97, 6)
        change_24h = float(signal.get("price_change_percentage_24h", 0))
        probability = signal.get("probability", "?")
        fallback_note = "\n⚠️ Сигнал из резервного режима (упрощённый фильтр)" if signal.get("fallback") else ""

        message = (
            f"*\ud83d\ude80 Сигнал на покупку: {signal['symbol']}*\n\n"
            f"*Цена входа:* ${fnum(price)}\n"
            f"*Цель:* +5% \u2192 ${fnum(target_price)}\n"
            f"*Стоп-лосс:* -3% \u2192 ${fnum(stop_price)}\n"
            f"*Изменение за 24ч:* {fnum(change_24h)}%\n"
            f"*Вероятность роста:* {probability}%\n"
            f"{fallback_note}"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("\ud83d\udd14 Следить за монетой", callback_data=f"track_{signal['symbol']}")]
        ])
        await context.bot.send_message(chat_id=user_id, text=message, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=user_id, text="Нет подходящих сигналов на текущий момент.")


def schedule_daily_signal_check(app, owner_id):
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")

    scheduler.add_job(lambda: app.create_task(send_signal_message(owner_id, app)),
                      trigger='cron', hour=8, minute=0, id='daily_signal')

    scheduler.add_job(lambda: app.create_task(refresh_signal_cache_job(app)),
                      trigger='interval', hours=3, id='refresh_signal_cache')

    scheduler.start()


async def debug_cache_message(user_id, context):
    cached = load_cached_signals()
    used = load_used_symbols()
    cached_symbols = [c["symbol"] for c in cached]
    unused = [s for s in cached_symbols if s not in used]

    msg = f"*\ud83d\udce6 Кеш сигналов:*\n"
    msg += f"Всего в кеше: {len(cached_symbols)} монет\n"
    msg += f"Использованы: {', '.join(used) if used else '—'}\n"
    msg += f"Остались: {', '.join(unused) if unused else '—'}"

    await context.bot.send_message(chat_id=user_id, text=msg, parse_mode="Markdown")


async def debug_analysis_message(user_id, context):
    if not ANALYSIS_LOG:
        await context.bot.send_message(chat_id=user_id, text="⏳ Анализ ещё не выполнялся.")
    else:
        msg = "*\ud83d\udcca Отладка анализа монет:*\n\n" + "\n".join(ANALYSIS_LOG[-50:])
        await context.bot.send_message(chat_id=user_id, text=msg, parse_mode="Markdown")
