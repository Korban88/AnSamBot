# crypto_utils.py

import httpx
import time
import json
import os
from crypto_list import TELEGRAM_WALLET_CRYPTOS

CACHE_FILE = "price_cache.json"
CACHE_TTL = 300  # 5 минут
BATCH_SIZE = 10  # до 10 монет за запрос
BATCH_DELAY = 1  # задержка между батчами (в секундах)

def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

def _fetch_market_data(coin_ids):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
        "price_change_percentage": "24h"
    }

    try:
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        print(f"Ошибка запроса: {e}")
        return []
    except httpx.HTTPStatusError as e:
        print(f"Ошибка статуса: {e.response.status_code}")
        return []

def _simulate_rsi(coin):
    change = coin.get("price_change_percentage_24h", 0)
    if change is None:
        return 50
    if change > 5:
        return 25 + (50 - min(change * 2, 50))
    elif change < -5:
        return 70 + min(abs(change * 2), 30)
    return 50

def _update_cache_all():
    cache = _load_cache()
    timestamp = int(time.time())

    for i in range(0, len(TELEGRAM_WALLET_CRYPTOS), BATCH_SIZE):
        batch = TELEGRAM_WALLET_CRYPTOS[i:i + BATCH_SIZE]
        fresh_data = _fetch_market_data(batch)
        if not fresh_data:
            continue

        for coin in fresh_data:
            coin_id = coin["id"]
            cache[coin_id] = {
                "timestamp": timestamp,
                "price": coin.get("current_price"),
                "change_24h": coin.get("price_change_percentage_24h"),
                "rsi": _simulate_rsi(coin),
                "ma": coin.get("moving_average_200d") or coin.get("current_price")
            }

        time.sleep(BATCH_DELAY)

    _save_cache(cache)

def _get_cached_value(coin_id, field):
    cache = _load_cache()
    entry = cache.get(coin_id)
    if not entry:
        return None
    if int(time.time()) - entry["timestamp"] > CACHE_TTL:
        return None
    return entry.get(field)

def _ensure_cache():
    cache = _load_cache()
    now = int(time.time())
    needs_update = any(
        (coin_id not in cache or now - cache[coin_id]["timestamp"] > CACHE_TTL)
        for coin_id in TELEGRAM_WALLET_CRYPTOS
    )
    if needs_update:
        _update_cache_all()

def get_current_price(coin_id):
    _ensure_cache()
    return _get_cached_value(coin_id, "price")

def get_24h_change(coin_id):
    _ensure_cache()
    return _get_cached_value(coin_id, "change_24h")

def get_rsi(coin_id):
    _ensure_cache()
    return _get_cached_value(coin_id, "rsi")

def get_ma(coin_id):
    _ensure_cache()
    return _get_cached_value(coin_id, "ma")
