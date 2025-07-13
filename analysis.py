import json
import os
import time

CACHE_FILE = "top_signals_cache.json"
CACHE_TTL = 12 * 60 * 60  # 12 часов в секундах

async def get_top_signals():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            data = json.load(file)
            if time.time() - data["timestamp"] < CACHE_TTL:
                return data["signals"]

    # Заглушка для новых сигналов
    new_signals = [
        {
            "id": "bitcoin",
            "name": "Bitcoin",
            "probability": 75,
            "entry_price": 30000,
            "target_price": 31500,
            "stop_loss": 29000,
        },
        {
            "id": "ton",
            "name": "Toncoin",
            "probability": 68,
            "entry_price": 7,
            "target_price": 7.35,
            "stop_loss": 6.7,
        },
        {
            "id": "ethereum",
            "name": "Ethereum",
            "probability": 65,
            "entry_price": 2000,
            "target_price": 2100,
            "stop_loss": 1950,
        },
    ]

    with open(CACHE_FILE, "w") as file:
        json.dump({"timestamp": time.time(), "signals": new_signals}, file)

    return new_signals
