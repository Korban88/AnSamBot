import json
import os
import time
from crypto_utils import get_change_and_price_batch, get_rsi_mock
from crypto_list import CRYPTO_LIST

CACHE_FILE = "top_signals_cache.json"
CACHE_EXPIRATION = 30 * 60  # 30 минут

def load_cached_top_signals():
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE, "r") as f:
        cache_data = json.load(f)
    if time.time() - cache_data["timestamp"] > CACHE_EXPIRATION:
        return None
    return cache_data["top_signals"]

def save_cached_top_signals(top_signals):
    cache_data = {
        "timestamp": time.time(),
        "top_signals": top_signals
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_data, f)

async def analyze_cryptos():
    cached = load_cached_top_signals()
    if cached:
        return cached

    crypto_ids = [crypto['id'] for crypto in CRYPTO_LIST]
    change_and_price_data = await get_change_and_price_batch(crypto_ids)

    signals = []
    for crypto in CRYPTO_LIST:
        coin_id = crypto['id']
        name = crypto['name']
        data = change_and_price_data.get(coin_id, {})
        price = data.get("price", 0.0)
        change_24h = data.get("change_24h", 0.0)

        if price <= 0:
            continue

        rsi = await get_rsi_mock(coin_id)

        if change_24h < -3.0:
            continue

        score = 0

        if 35 <= rsi <= 65:
            score += 1
        if change_24h >= 0:
            score += 1

        probability = min(50 + score * 10, 90)

        signals.append({
            "name": name,
            "id": coin_id,
            "price": round(price, 4),
            "change_24h": round(change_24h, 2),
            "rsi": rsi,
            "probability": probability
        })

    signals.sort(key=lambda x: x['probability'], reverse=True)

    top_signals = signals[:3]

    save_cached_top_signals(top_signals)

    return top_signals

# Добавлено для совместимости с handlers.py
async def get_top_signals():
    return await analyze_cryptos()
