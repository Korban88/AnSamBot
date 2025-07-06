import aiohttp
import json
import os
from datetime import datetime, timedelta
from crypto_list import crypto_list

RSI_PERIOD = 14
MA_PERIOD = 7
CACHE_FILE = "indicators_cache.json"

# Загрузка кэша
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохранение кэша
def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

# Исторические цены
async def fetch_historical_prices(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": "7",
        "interval": "hourly"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return [price[1] for price in data.get("prices", [])]
            return []

# RSI
def calculate_rsi(prices):
    if len(prices) < RSI_PERIOD + 1:
        return None
    gains = []
    losses = []
    for i in range(1, RSI_PERIOD + 1):
        delta = prices[-i] - prices[-i - 1]
        if delta >= 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))
    average_gain = sum(gains) / RSI_PERIOD if gains else 0
    average_loss = sum(losses) / RSI_PERIOD if losses else 0
    if average_loss == 0:
        return 100
    rs = average_gain / average_loss
    return round(100 - (100 / (1 + rs)), 2)

# MA
def calculate_moving_average(prices):
    if len(prices) < MA_PERIOD:
        return None
    return round(sum(prices[-MA_PERIOD:]) / MA_PERIOD, 4)

# Получение RSI с кэшем
async def get_rsi(coin_id):
    cache = load_cache()
    if coin_id in cache:
        cached = cache[coin_id]
        timestamp = datetime.fromisoformat(cached["timestamp"])
        if datetime.now() - timestamp < timedelta(minutes=30) and "rsi" in cached:
            return cached["rsi"]

    prices = await fetch_historical_prices(coin_id)
    rsi = calculate_rsi(prices)
    cache[coin_id] = cache.get(coin_id, {})
    cache[coin_id]["rsi"] = rsi
    cache[coin_id]["timestamp"] = datetime.now().isoformat()
    save_cache(cache)
    return rsi

# Получение MA с кэшем
async def get_moving_average(coin_id):
    cache = load_cache()
    if coin_id in cache:
        cached = cache[coin_id]
        timestamp = datetime.fromisoformat(cached["timestamp"])
        if datetime.now() - timestamp < timedelta(minutes=30) and "ma" in cached:
            return cached["ma"]

    prices = await fetch_historical_prices(coin_id)
    ma = calculate_moving_average(prices)
    cache[coin_id] = cache.get(coin_id, {})
    cache[coin_id]["ma"] = ma
    cache[coin_id]["timestamp"] = datetime.now().isoformat()
    save_cache(cache)
    return ma

# Получение текущей цены
async def get_current_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coin_id,
        "vs_currencies": "usd"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get(coin_id, {}).get("usd")
            return None

# Сбор данных по всем монетам
async def fetch_all_coin_data():
    data = []
    for coin in crypto_list:
        price = await get_current_price(coin["id"])
        ma = await get_moving_average(coin["id"])
        rsi = await get_rsi(coin["id"])
        if price and ma and rsi is not None:
            data.append({
                "id": coin["id"],
                "symbol": coin["symbol"],
                "price": price,
                "ma": ma,
                "rsi": rsi
            })
    return data
