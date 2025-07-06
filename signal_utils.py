from analysis import analyze_cryptos
from crypto_utils import fetch_all_coin_data
import random

signal_index = 0
top_signals_cache = []
active_trackings = []

async def get_next_signal_message():
    global signal_index, top_signals_cache

    if not top_signals_cache:
        coin_data = await fetch_all_coin_data()
        top_signals_cache = await analyze_cryptos(coin_data)

    if not top_signals_cache:
        raise ValueError("Нет подходящих сигналов.")

    if signal_index >= len(top_signals_cache):
        signal_index = 0  # Перезапускаем цикл по топ-3

    coin = top_signals_cache[signal_index]
    signal_index += 1

    coin_id = coin['id']
    symbol = coin['symbol'].upper()
    entry = coin['entry_price']
    target = coin['target_price']
    stop = coin['stop_loss']
    rsi = coin['rsi']
    ma = coin['ma']
    change_24h = coin['change_24h']
    score = coin['score']
    probability = coin['probability']

    message = (
        f"*💎 Сигнал на рост {symbol}*\n\n"
        f"*Вероятность роста:* {probability:.1f}%\n"
        f"*Цена входа:* {entry:.5f}\n"
        f"*Цель ( +5% ):* {target:.5f}\n"
        f"*Стоп-лосс:* {stop:.5f}\n\n"
        f"*📊 RSI:* {rsi} — {'перекуплен' if rsi > 70 else 'перепродан' if rsi < 30 else 'норма'}\n"
        f"*📈 MA:* {ma:.5f}\n"
        f"*📉 24ч:* {change_24h:+.2f}%\n"
    )

    return message, coin_id, entry

def reset_signal_index():
    global signal_index
    signal_index = 0

def stop_all_tracking():
    global active_trackings
    active_trackings = []
