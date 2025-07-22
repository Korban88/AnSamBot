import aiohttp
import json
import os
import random
from datetime import datetime, timedelta

CACHE_PATH = "indicators_cache.json"

# Загрузка или инициализация кеша
if os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, "r") as f:
        INDICATOR_CACHE = json.load(f)
else:
    INDICATOR_CACHE = {}

def save_cache():
    with open(CACHE_PATH, "w") as f:
        json.dump(INDICATOR_CACHE, f)

def simulate_rsi(price_change):
    """Грубая симуляция RSI на основе 24h изменений"""
    if price_change >= 10:
        return random.randint(65, 75)
    elif price_change >= 5:
        return random.randint(55, 65)
    elif price_change >= 0:
        return random.randint(45, 55)
    elif price_change >= -3:
        return random.randint(35, 45)
    else:
        return random.randint(25, 35)

def simulate_ma7(current_price):
    """Симулируем MA7 немного ниже текущей цены"""
    variation = random.uniform(-0.03, 0.03)
    return round(current_price * (1 - variation), 4)

async def fetch_all_coin_data(coin_ids):
    url = f"https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
        "price_change_percentage": "24h"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                return []

async def get_all_coin_data(coin_ids):
    """
    Получает данные по монетам и дополняет их RSI и MA7 (с кешем).
    """
    raw_data = await fetch_all_coin_data(coin_ids)
    result = []

    for coin in raw_data:
        coin_id = coin["id"]
        current_price = coin.get("current_price")
        change_24h = coin.get("price_change_percentage_24h", 0)

        # Кеш по времени
        cached = INDICATOR_CACHE.get(coin_id, {})
        timestamp = cached.get("timestamp")
        now = datetime.utcnow()
        is_fresh = timestamp and (now - datetime.fromisoformat(timestamp)) < timedelta(hours=1)

        if is_fresh:
            coin["rsi"] = cached["rsi"]
            coin["ma7"] = cached["ma7"]
        else:
            rsi = simulate_rsi(change_24h)
            ma7 = simulate_ma7(current_price)
            coin["rsi"] = rsi
            coin["ma7"] = ma7
            INDICATOR_CACHE[coin_id] = {
                "rsi": rsi,
                "ma7": ma7,
                "timestamp": now.isoformat()
            }

        result.append(coin)

    save_cache()
    return result

async def get_price(symbol):
    """
    Получает текущую цену монеты по её символу.
    """
    from crypto_list import TELEGRAM_WALLET_COIN_IDS

    coin_id = None
    for id_, sym in TELEGRAM_WALLET_COIN_IDS.items():
        if sym.lower() == symbol.lower():
            coin_id = id_
            break

    if not coin_id:
        return None

    coins = await get_all_coin_data([coin_id])
    if coins and coins[0]:
        return coins[0].get("current_price")
    return None
