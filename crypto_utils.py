import httpx
import time
import json
import os
from crypto_list import TELEGRAM_WALLET_CRYPTOS

CACHE_FILE = "price_cache.json"
CACHE_TTL = 300  # 5 минут

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

def _fetch_market_data_block(coin_ids_block):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids_block),
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

def _update_cache_all():
    all_ids = TELEGRAM_WALLET_CRYPTOS
    blocks = [all_ids[i:i + 10] for i in range(0, len(all_ids), 10)]

    combined_data = []
    for block in blocks:
        data = _fetch_market_data_block(block)
        if data:
            combined_data.extend(data)
        time.sleep(1.5)  # пауза между запросами, чтобы не ловить 429

    if not combined_data:
        return {}

    cache = _load_cache()
    timestamp = int(time.time())

    for coin in combined_data:
        coin_id = coin["id"]
        cache[coin_id] = {
            "timestamp": timestamp,
            "price": coin.get("current_price"),
            "change_24h": coin.get("price_change_percentage_24h"),
            "rsi": _simulate_rsi(coin),
            "ma": coin.get("moving_average_200d") or coin.get("current_price")  # заглушка
        }

    _save_cache(cache)
    return cache

def _simulate_rsi(coin):
    change = coin.get("price_change_percentage_24h", 0)
    if change is None:
        return 50
    if change > 5:
        return 25 + (50 - min(change * 2, 50))
    elif change < -5:
        return 70 + min(abs(change * 2), 30)
    return 50

def _get_cached_value(coin_id, field):
    cache = _load_cache()
    entry = cache.get(coin_id)
    if not entry:
        return None
    if int(time.time()) - entry["timestamp"] > CACHE_TTL:
        return None
    return entry.get(field)

def get_current_price(coin_id):
    value = _get_cached_value(coin_id, "price")
    if value is None:
        _update_cache_all()
        value = _get_cached_value(coin_id, "price")
    return value

def get_24h_change(coin_id):
    value = _get_cached_value(coin_id, "change_24h")
    if value is None:
        _update_cache_all()
        value = _get_cached_value(coin_id, "change_24h")
    return value

def get_rsi(coin_id):
    value = _get_cached_value(coin_id, "rsi")
    if value is None:
        _update_cache_all()
        value = _get_cached_value(coin_id, "rsi")
    return value

def get_ma(coin_id):
    value = _get_cached_value(coin_id, "ma")
    if value is None:
        _update_cache_all()
        value = _get_cached_value(coin_id, "ma")
    return value
