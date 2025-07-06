import json
import os
import random

from analysis import analyze_cryptos
from crypto_utils import fetch_all_coin_data
from crypto_list import crypto_list

signal_index = 0

def reset_signal_index():
    global signal_index
    signal_index = 0

async def get_next_signal_message():
    global signal_index

    coin_data = await fetch_all_coin_data()
    top_cryptos = await analyze_cryptos(coin_data)

    if not top_cryptos:
        return "⚠️ Не удалось найти подходящие монеты для сигнала.", None, None

    if signal_index >= len(top_cryptos):
        signal_index = 0

    selected = top_cryptos[signal_index]
    signal_index += 1

    coin_id = selected["id"]
    symbol = selected["symbol"]
    entry_price = round(selected["price"], 4)
    target_price = round(entry_price * 1.05, 4)
    stop_loss_price = round(entry_price * 0.96, 4)

    explanation = (
        f"*🔔 Сигнал по монете:* `{symbol.upper()}`\n\n"
        f"*🎯 Цель:* +5%\n"
        f"*🔹 Вход:* `{entry_price}`\n"
        f"*🛑 Стоп-лосс:* `{stop_loss_price}`\n"
        f"*📈 Целевая цена:* `{target_price}`\n\n"
        f"*📊 Вероятность роста:* `{selected['probability']}%`\n\n"
        f"*MA:* {round(selected['ma'], 4)}\n"
        f"*RSI:* {round(selected['rsi'], 2)}\n"
        f"*Изменение за 24ч:* {round(selected['change_24h'], 2)}%\n"
    )

    return explanation, coin_id, entry_price
