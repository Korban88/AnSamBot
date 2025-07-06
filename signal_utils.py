import json
from analysis import analyze_cryptos
from crypto_utils import fetch_all_coin_data
from utils import escape_markdown
from tracking import start_tracking
from config import TELEGRAM_USER_ID

signal_index = 0
top_cryptos_cache = []

async def get_next_signal_message():
    global signal_index, top_cryptos_cache

    if not top_cryptos_cache:
        coin_data = await fetch_all_coin_data()
        top_cryptos_cache = await analyze_cryptos(coin_data)

    if not top_cryptos_cache:
        return "⚠️ Нет подходящих монет для сигнала.", None, None

    if signal_index >= len(top_cryptos_cache):
        signal_index = 0

    signal = top_cryptos_cache[signal_index]
    signal_index += 1

    coin_id = signal["coin_id"]
    name = escape_markdown(signal["name"])
    symbol = escape_markdown(signal["symbol"])
    current_price = signal["current_price"]
    entry_price = round(current_price * 0.995, 4)
    target_price = round(current_price * 1.05, 4)
    stop_loss_price = round(current_price * 0.97, 4)
    growth_probability = signal["growth_probability"]
    rsi = signal.get("rsi", "N/A")
    ma = signal.get("ma", "N/A")
    price_change_24h = signal.get("price_change_percentage_24h", "N/A")

    explanation = f"\n📈 RSI: {rsi}\n📊 MA: {ma}\n📉 24h: {price_change_24h}%"

    message = (
        f"*💹 Сигнал на рост монеты: {name} ({symbol})*\n"
        f"Вероятность роста: *{growth_probability}%*\n\n"
        f"Цена входа: *{entry_price}*\n"
        f"Цель (+5%): *{target_price}*\n"
        f"Стоп-лосс: *{stop_loss_price}*"
        f"{explanation}"
    )

    return message, coin_id, entry_price

def reset_signal_index():
    global signal_index
    signal_index = 0
