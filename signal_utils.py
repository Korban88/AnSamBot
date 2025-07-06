import random
from analysis import analyze_cryptos
from crypto_utils import fetch_all_coin_data

signal_index = 0

async def get_next_signal_message():
    global signal_index

    coin_data = await fetch_all_coin_data()
    top_cryptos = await analyze_cryptos(coin_data)

    if not top_cryptos:
        return "❌ Не удалось найти подходящие монеты.", None, None

    crypto = top_cryptos[signal_index % len(top_cryptos)]
    signal_index += 1

    coin_id = crypto["id"]
    symbol = crypto["symbol"]
    entry_price = crypto["price"]
    target_price = round(entry_price * 1.05, 4)
    stop_loss = round(entry_price * 0.97, 4)
    probability = crypto["probability"]
    rsi = crypto["rsi"]
    ma = crypto["ma"]
    change_24h = crypto["change_24h"]

    message = (
        f"*💰 Сигнал на покупку: {symbol.upper()}*\n\n"
        f"*🎯 Цель:* +5%\n"
        f"*🔹 Текущая цена:* ${entry_price}\n"
        f"*📈 Целевая цена:* ${target_price}\n"
        f"*🛡️ Стоп-лосс:* ${stop_loss}\n\n"
        f"*📊 Вероятность роста:* {probability}%\n"
        f"*RSI:* {rsi}\n"
        f"*MA (7д):* {ma}\n"
        f"*Изменение за 24ч:* {change_24h}%"
    )

    return message, coin_id, entry_price

def reset_signal_index():
    global signal_index
    signal_index = 0
