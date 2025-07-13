import json
import os
import logging
from datetime import datetime, timedelta
from crypto_utils import get_change_and_price_batch, get_rsi_mock
from crypto_list import CRYPTO_LIST

CACHE_FILE = "top_signals_cache.json"
CACHE_DURATION_MINUTES = 30

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except Exception as e:
                logging.error(f"Ошибка загрузки кеша: {e}")
    return {}

def save_cache(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file)

async def analyze_cryptos():
    cache = load_cache()
    now = datetime.utcnow()

    if "timestamp" in cache:
        cache_time = datetime.fromisoformat(cache["timestamp"])
        if now - cache_time < timedelta(minutes=CACHE_DURATION_MINUTES):
            logging.info("Загружаем top_signals из кеша")
            logging.info(f"Кешированные монеты: {[coin['coin'] for coin in cache.get('top_signals', [])]}")
            return cache.get("top_signals", [])

    try:
        price_data = await get_change_and_price_batch(CRYPTO_LIST)
    except Exception as e:
        logging.error(f"Ошибка анализа: {e}")
        return []

    signals = []
    for coin_id in CRYPTO_LIST:
        rsi = await get_rsi_mock(coin_id)
        change_24h = price_data[coin_id]["change_24h"]
        price = price_data[coin_id]["price"]

        probability = 50
        if rsi < 30 and change_24h > -1:
            probability = 75
        elif rsi < 40:
            probability = 65
        elif rsi > 70:
            probability = 40

        if change_24h < -3:
            probability -= 15

        signals.append({
            "coin": coin_id,
            "price": round(price, 2),
            "change_24h": round(change_24h, 2),
            "probability": probability
        })

    filtered_signals = [s for s in signals if s["probability"] >= 55]
    logging.info(f"Отобрано монет с probability >= 55: {len(filtered_signals)}")
    for s in filtered_signals:
        logging.info(f"{s['coin']} — Вероятность: {s['probability']}% Цена: {s['price']}")

    if len(filtered_signals) < 3:
        logging.warning("Внимание: в top_signals меньше 3 монет!")

    sorted_signals = sorted(filtered_signals, key=lambda x: x["probability"], reverse=True)
    top_signals = sorted_signals[:3]

    cache = {
        "timestamp": now.isoformat(),
        "top_signals": top_signals
    }
    save_cache(cache)

    return top_signals
