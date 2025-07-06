# signal_utils.py

from analysis import analyze_cryptos
from tracking import start_tracking
from config import TELEGRAM_USER_ID

signal_index = 0
top_cryptos_cache = []

async def get_next_signal_message():
    global signal_index, top_cryptos_cache

    if not top_cryptos_cache:
        top_cryptos_cache = await analyze_cryptos()
        signal_index = 0

    if signal_index >= len(top_cryptos_cache):
        signal_index = 0

    crypto = top_cryptos_cache[signal_index]
    signal_index += 1

    name = crypto["name"]
    symbol = crypto["symbol"].upper()
    price = crypto["price"]
    target = crypto["target_price"]
    stop_loss = crypto["stop_loss"]
    probability = crypto["probability"]
    reason = crypto.get("reason", "")

    message = (
        f"📈 *Сигнал на рост {symbol}*\n\n"
        f"Монета: *{name} ({symbol})*\n"
        f"Текущая цена: *${price}*\n"
        f"Цель: *${target}* (+5%)\n"
        f"Стоп-лосс: *${stop_loss}*\n"
        f"Вероятность роста: *{probability}%*\n"
    )

    if reason:
        message += f"\nПричина: _{reason}_"

    return message, name, price, target, stop_loss, probability

def reset_signal_index():
    global signal_index
    signal_index = 0
