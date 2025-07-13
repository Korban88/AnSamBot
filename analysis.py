import json
import os
import time
from crypto_list import CRYPTO_LIST

CACHE_FILE = "top_signals_cache.json"
CACHE_TTL = 12 * 60 * 60  # 12 часов в секундах

def calculate_probability(change_24h: float, rsi: float) -> int:
    probability = 50

    if change_24h > 0:
        probability += min(change_24h * 2, 10)  # Максимум +10%
    else:
        probability += max(change_24h * 2, -10)  # Максимум -10%

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

    new_signals = []
    for coin in CRYPTO_LIST[:3]:
        # Пока используем фиктивные значения change_24h и rsi
        fake_change_24h = 2.5
        fake_rsi = 55
        probability = calculate_probability(fake_change_24h, fake_rsi)

        new_signals.append({
            "id": coin["id"],
            "name": coin["name"],
            "probability": probability,
            "entry_price": 100,
            "target_price": 105,
            "stop_loss": 95,
        })

    with open(CACHE_FILE, "w") as file:
        json.dump({"timestamp": time.time(), "signals": new_signals}, file)

    return new_signals
