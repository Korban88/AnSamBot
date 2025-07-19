import aiohttp
import json
import os
from datetime import datetime, timedelta

INDICATORS_CACHE_FILE = "indicators_cache.json"


async def get_current_prices(crypto_ids):
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={','.join(crypto_ids)}"
        "&vs_currencies=usd"
        "&include_24hr_change=true"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Ошибка при получении цен: {response.status}")
                return {}
            return await response.json()


def load_indicators_cache():
    if os.path.exists(INDICATORS_CACHE_FILE):
        with open(INDICATORS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_indicators_cache(cache):
    with open(INDICATORS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def is_cache_expired(timestamp_str, ttl_minutes=10):
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        return datetime.utcnow() - timestamp > timedelta(minutes=ttl_minutes)
    except Exception:
        return True


def get_cached_indicator(cache, coin_id, indicator):
    data = cache.get(coin_id, {})
    if indicator in data and not is_cache_expired(data[indicator]["timestamp"]):
        return data[indicator]["value"]
    return None


def set_cached_indicator(cache, coin_id, indicator, value):
    if coin_id not in cache:
        cache[coin_id] = {}
    cache[coin_id][indicator] = {
        "value": value,
        "timestamp": datetime.utcnow().isoformat()
    }


def reset_top_signals_cache():
    try:
        os.remove("top_signals_cache.json")
    except FileNotFoundError:
        pass
