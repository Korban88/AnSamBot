import aiohttp
import asyncio
import json
import time
import os

INDICATORS_CACHE_FILE = "indicators_cache.json"

async def fetch_coin_data(session, coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false&sparkline=false"
    try:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()
            market_data = data.get("market_data", {})
            return {
                "current_price": market_data.get("current_price", {}).get("usd"),
                "change_24h": market_data.get("price_change_percentage_24h"),
                "volume": market_data.get("total_volume", {}).get("usd")
            }
    except Exception:
        return None

def load_cached_indicators():
    if os.path.exists(INDICATORS_CACHE_FILE):
        with open(INDICATORS_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cached_indicators(data):
    with open(INDICATORS_CACHE_FILE, "w") as f:
        json.dump(data, f)

async def fetch_rsi_ma(session, coin_id):
    # ⚠️ Заглушка: замени на реальный источник данных RSI/MA при подключении
    return {
        "rsi": 45 + hash(coin_id) % 20,      # от 45 до 65
        "ma": 1.01,                          # условно MA = 1.01 USDT
    }

async def get_market_data(coin_ids):
    cache = load_cached_indicators()
    now = time.time()
    updated = {}
    results = {}

    async with aiohttp.ClientSession() as session:
        tasks = []
        for coin in coin_ids:
            coin_id = coin.lower()
            coin_cached = cache.get(coin_id, {})
            if not coin_cached or now - coin_cached.get("timestamp", 0) > 3600:
                tasks.append((coin_id, fetch_coin_data(session, coin_id)))
            else:
                results[coin] = coin_cached["data"]

        fetched = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

        for (coin_id, _), data in zip(tasks, fetched):
            if isinstance(data, dict):
                indicators = await fetch_rsi_ma(session, coin_id)
                combined = {**data, **indicators}
                results[coin_id] = combined
                updated[coin_id] = {
                    "timestamp": now,
                    "data": combined
                }

    if updated:
        cache.update(updated)
        save_cached_indicators(cache)

    return results
