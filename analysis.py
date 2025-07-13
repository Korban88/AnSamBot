import json
import os
import logging
from datetime import datetime, timedelta
from crypto_utils import get_change_and_price_batch, get_rsi_mock
from crypto_list import CRYPTO_LIST

logger = logging.getLogger(__name__)

CACHE_FILE = "top_signals_cache.json"
CACHE_EXPIRY_MINUTES = 30

def load_cached_top_signals():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            timestamp = datetime.fromisoformat(cache_data["timestamp"])
            if datetime.now() - timestamp < timedelta(minutes=CACHE_EXPIRY_MINUTES):
                logger.info("Загружаем топ-сигналы из кеша")
                return cache_data["top_signals"]
    return None

def save_cached_top_signals(top_signals):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "top_signals": top_signals
        }, f, ensure_ascii=False, indent=4)

async def analyze_cryptos(coin_ids: list) -> list:
    cached_signals = load_cached_top_signals()
    if cached_signals:
        return cached_signals

    logger.info(f"Анализируем {len(coin_ids)} монет...")

    try:
        change_and_price = await get_change_and_price_batch(coin_ids)
    except Exception as e:
        logger.error(f"Ошибка при получении данных о ценах и изменениях: {e}")
        return []

    top_signals = []

    for coin_id in coin_ids:
        price_info = change_and_price.get(coin_id, {})
        change_24h = price_info.get("change_24h", 0.0)
        price = price_info.get("price", 0.0)

        rsi = await get_rsi_mock(coin_id)

        probability = 70 + (rsi - 50) * 0.5 - abs(change_24h) * 0.2
        probability = max(0, min(100, probability))

        logger.info(f"{coin_id} → price: {price}, change_24h: {change_24h}, rsi: {rsi}, probability: {probability}")

        if probability >= 65 and change_24h > -3:
            top_signals.append({
                "coin_id": coin_id,
                "price": price,
                "change_24h": change_24h,
                "rsi": rsi,
                "probability": round(probability, 2)
            })
        else:
            logger.info(f"{coin_id} отсеян: probability={probability}, change_24h={change_24h}")

    top_signals = sorted(top_signals, key=lambda x: x["probability"], reverse=True)[:3]

    save_cached_top_signals(top_signals)

    logger.info(f"Топ сигналов после фильтрации: {top_signals}")

    return top_signals

async def get_top_signals():
    return await analyze_cryptos(CRYPTO_LIST)
