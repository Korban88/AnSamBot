import json
import os
import time
from crypto_list import CRYPTO_LIST
from crypto_utils import get_change_and_price_batch, get_rsi_mock

CACHE_FILE = "top_signals_cache.json"
CACHE_TTL = 12 * 60 * 60  # 12 часов в секундах

def calculate_probability(change_24h: float, rsi: float) -> int:
    probability = 50

    if change_24h > 0:
        probability += min(change_24h * 2, 10)
    else:
        probability += max(change_24h * 2, -10)

    if 30 < rsi < 70:
        probability += 15
    elif rsi <= 30:
        probability -= 10
    elif rsi >= 70:
        probability -= 10

    probability = max(1, min(int(probability), 99))

    return probability

async def get_top_signals():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            data = json.load(file)
            if time.time() - data["timestamp"] < CACHE_TTL:
                return data["signals"]

    coin_ids = [coin["id"] for coin in CRYPTO_LIST]
    change_and_price_dict = await get_change_and_price_batch(coin_ids)

    all_signals = []
    for coin in CRYPTO_LIST:
        stats = change_and_price_dict.get(coin["id"], {"change_24h": 0.0, "price": 100.0})
        change_24h = stats["change_24h"]
        entry_price = stats["price"]
        rsi = await get_rsi_mock(coin["id"])
        probability = calculate_probability(change_24h, rsi)

        if probability >= 65 and change_24h >= -3 and entry_price > 0:
            all_signals.append({
                "id": coin["id"],
                "name": coin["name"],
                "probability": probability,
                "entry_price": round(entry_price, 2),
                "target_price": round(entry_price * 1.05, 2),
                "stop_loss": round(entry_price * 0.95, 2),
            })

    top_signals = sorted(all_signals, key=lambda x: x["probability"], reverse=True)[:3]

    with open(CACHE_FILE, "w") as file:
        json.dump({"timestamp": time.time(), "signals": top_signals}, file)

    return top_signals
