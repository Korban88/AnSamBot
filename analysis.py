import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from crypto_utils import get_change_and_price_batch
from crypto_list import CRYPTO_LIST, CRYPTO_IDS

CACHE_FILE = "top_signals_cache.json"
CACHE_DURATION_MINUTES = 30

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analysis")


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache_data):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_data, f)


def is_cache_valid(timestamp_str):
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return datetime.now() - timestamp < timedelta(minutes=CACHE_DURATION_MINUTES)
    except Exception:
        return False


async def get_top_signals():
    cache_data = load_cache()
    if cache_data.get("timestamp") and is_cache_valid(cache_data["timestamp"]):
        logger.info("Загружаем топ монет из кеша")
        return cache_data["signals"]

    logger.info(f"Анализируем {len(CRYPTO_IDS)} монет...")

    try:
        prices_changes = await get_change_and_price_batch(CRYPTO_IDS)
    except Exception as e:
        logger.error(f"Ошибка при получении данных о ценах и изменениях: {e}")
        return []

    signals = []
    for coin in CRYPTO_LIST:
        coin_id = coin["id"]
        price_info = prices_changes.get(coin_id)

        if not price_info or price_info["price"] == 0:
            continue

        change_24h = price_info["change_24h"]
        price = price_info["price"]

        if change_24h <= -3:
            continue

        probability = round(min(max(50 + change_24h, 0), 100), 2)

        signals.append({
            "id": coin_id,
            "name": coin["name"],
            "entry_price": round(price, 4),
            "target_price": round(price * 1.05, 4),
            "stop_loss": round(price * 0.97, 4),
            "probability": probability
        })

    signals.sort(key=lambda x: x["probability"], reverse=True)
    top_signals = signals[:3]

    cache_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "signals": top_signals
    }
    save_cache(cache_data)

    logger.info(f"Топ монет сформирован: {[coin['name'] for coin in top_signals]}")
    return top_signals


if __name__ == "__main__":
    result = asyncio.run(get_top_signals())
    print(result)
