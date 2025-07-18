import json
import logging
import os
import time
from crypto_list import CRYPTO_LIST
from crypto_utils import get_change_and_price_batch

TOP_SIGNALS_CACHE_FILE = "top_signals_cache.json"
CACHE_TTL_SECONDS = 1800  # 30 минут

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analysis")

def load_top_signals_cache():
    if os.path.exists(TOP_SIGNALS_CACHE_FILE):
        with open(TOP_SIGNALS_CACHE_FILE, "r") as f:
            try:
                data = json.load(f)
                timestamp = data.get("timestamp", 0)
                if time.time() - timestamp < CACHE_TTL_SECONDS:
                    return data.get("top_signals", [])
            except Exception as e:
                logger.error(f"Ошибка при чтении кеша топ сигналов: {e}")
    return []

def save_top_signals_cache(top_signals):
    with open(TOP_SIGNALS_CACHE_FILE, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "top_signals": top_signals
        }, f)

def clear_top_signals_cache():
    if os.path.exists(TOP_SIGNALS_CACHE_FILE):
        os.remove(TOP_SIGNALS_CACHE_FILE)
        logger.info("Кеш топ сигналов сброшен.")

async def get_top_signals():
    cached_signals = load_top_signals_cache()
    if cached_signals:
        logger.info(f"Возвращаем топ сигналы из кеша: {[coin['name'] for coin in cached_signals]}")
        return cached_signals

    logger.info(f"Анализируем {len(CRYPTO_LIST)} монет...")
    coin_ids = [coin['id'] for coin in CRYPTO_LIST]
    price_and_change = await get_change_and_price_batch(coin_ids)

    if not price_and_change:
        logger.error("Не удалось получить данные о ценах и изменениях.")
        return []

    results = []
    for coin in CRYPTO_LIST:
        coin_id = coin['id']
        name = coin['name']
        info = price_and_change.get(coin_id, {})
        if "price" not in info or "change_24h" not in info:
            logger.warning(f"Нет данных для {coin_id}, пропускаем.")
            continue
        price = info.get("price", 0.0)
        change_24h = info.get("change_24h", 0.0)
        if change_24h > -3:
            growth_probability = min(95, max(65, 70 + change_24h))
            entry_price = price
            target_price = round(price * 1.05, 4)
            stop_loss = round(price * 0.97, 4)
            results.append({
                "id": coin_id,
                "name": name,
                "price": round(price, 4),
                "entry_price": entry_price,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "change_24h": round(change_24h, 4),
                "growth_probability": round(growth_probability, 2)
            })
    results.sort(key=lambda x: x["growth_probability"], reverse=True)
    top_signals = results[:3]
    save_top_signals_cache(top_signals)
    logger.info(f"Топ монет сформирован: {[coin['name'] for coin in top_signals]}")
    return top_signals
