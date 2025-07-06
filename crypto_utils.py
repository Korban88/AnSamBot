import aiohttp
import json
import os
from datetime import datetime, timedelta

CACHE_PATH = "indicators_cache.json"

async def fetch_all_coin_data(coin_ids):
    url = f"https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
        "price_change_percentage": "24h"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            return await response.json()

async def get_current_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin_id, "vs_currencies": "usd"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            return data[coin_id]["usd"]

async def get_rsi(coin_id):
    return 50.0  # заглушка

async def get_moving_average(coin_id):
    return 1.0  # заглушка
