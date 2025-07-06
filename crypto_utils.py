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
            data = await response.json()

            # Преобразуем список в словарь по coin_id
            return {
                coin["id"]: {
                    "price": coin["current_price"],
                    "change_24h": coin.get("price_change_percentage_24h")
                }
                for coin in data
                if "id" in coin and "current_price" in coin
            }

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
