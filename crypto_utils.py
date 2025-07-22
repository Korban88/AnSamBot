import aiohttp
import json
import os
from datetime import datetime, timedelta

CACHE_FILE = "indicators_cache.json"
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
VS_CURRENCY = "usd"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

async def fetch_market_data(coin_ids):
    url = COINGECKO_URL
    params = {
        "vs_currency": VS_CURRENCY,
        "ids": ",".join(coin_ids),
        "price_change_percentage": "24h",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            return []

async def fetch_rsi_and_ma(coin_id):
    # В реальном варианте сюда можно подключить анализ с TradingView или по API биржи
    # Здесь мы эмулируем реалистичные данные
    import random
    return {
        "rsi": round(random.uniform(40, 65), 2),
        "ma7": round(random.uniform(0.95, 1.05), 4)
    }

async def get_all_coin_data(coin_ids):
    cache = load_cache()
    now = datetime.utcnow()
    result = []

    raw_data = await fetch_market_data(coin_ids)

    for coin in raw_data:
        coin_id = coin.get("id")
        if not coin_id:
            continue

        cached = cache.get(coin_id, {})
        cached_time = datetime.strptime(cached.get("timestamp", "1970-01-01"), "%Y-%m-%dT%H:%M:%S")

        if (now - cached_time) < timedelta(minutes=30):
            rsi = cached.get("rsi")
            ma7 = cached.get("ma7")
        else:
            indicators = await fetch_rsi_and_ma(coin_id)
            rsi = indicators["rsi"]
            ma7 = coin["current_price"] * indicators["ma7"]  # Эмуляция MA7 как отклонения от текущей цены

            cache[coin_id] = {
                "rsi": rsi,
                "ma7": ma7,
                "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S")
            }

        coin["rsi"] = rsi
        coin["ma7"] = ma7
        result.append(coin)

    save_cache(cache)
    return result
