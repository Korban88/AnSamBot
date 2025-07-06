import aiohttp
import time

BASE_URL = "https://api.coingecko.com/api/v3"

async def fetch_market_data(coin_id):
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": 1, "interval": "hourly"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("prices", [])

async def get_current_price(coin_id):
    url = f"{BASE_URL}/simple/price"
    params = {"ids": coin_id, "vs_currencies": "usd"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get(coin_id, {}).get("usd")

def parse_prices_with_timestamps(prices):
    result = []
    for price in prices:
        if not isinstance(price, list) or len(price) != 2:
            continue
        timestamp_ms, price_value = price
        try:
            timestamp = int(timestamp_ms) // 1000
        except Exception:
            continue
        result.append({
            "timestamp": timestamp,
            "price": price_value
        })
    return result
