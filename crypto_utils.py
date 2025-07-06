import aiohttp
import asyncio
import json
import os
from datetime import datetime, timedelta
from crypto_list import TELEGRAM_WALLET_COINS

INDICATORS_CACHE_FILE = "indicators_cache.json"

# Загрузка кеша
def load_indicators_cache():
    if os.path.exists(INDICATORS_CACHE_FILE):
        with open(INDICATORS_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохранение кеша
def save_indicators_cache(cache):
    with open(INDICATORS_CACHE_FILE, "w") as f:
        json.dump(cache, f)

indicators_cache = load_indicators_cache()

# Получение текущей цены
async def get_current_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data.get(coin_id, {}).get("usd")

# Получение RSI
async def get_rsi(coin_id, period=14):
    cache_key = f"{coin_id}_rsi"
    if cache_key in indicators_cache:
        return indicators_cache[cache_key]

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": period}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            prices = [price[1] for price in data.get("prices", [])]
            if len(prices) < period + 1:
                return None

            gains, losses = [], []
            for i in range(1, len(prices)):
                delta = prices[i] - prices[i - 1]
                if delta >= 0:
                    gains.append(delta)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(-delta)
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            indicators_cache[cache_key] = rsi
            save_indicators_cache(indicators_cache)
            return rsi

# Получение скользящей средней
async def get_moving_average(coin_id, days=14):
    cache_key = f"{coin_id}_ma_{days}"
    if cache_key in indicators_cache:
        return indicators_cache[cache_key]

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            prices = [price[1] for price in data.get("prices", [])]
            if not prices:
                return None
            ma = sum(prices) / len(prices)
            indicators_cache[cache_key] = ma
            save_indicators_cache(indicators_cache)
            return ma

# Получение всех текущих цен
async def fetch_all_current_prices():
    ids = ",".join(coin["id"] for coin in TELEGRAM_WALLET_COINS)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()
