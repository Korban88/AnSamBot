import aiohttp
import json
import os
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

def safe_float(value, default=0.0):
    """Безопасное преобразование в float"""
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def simulate_rsi(price_change):
    """Грубая симуляция RSI на основе 24h изменений"""
    import random
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
    import random
    variation = random.uniform(-0.03, 0.03)
    return round(safe_float(current_price) * (1 - variation), 4)

def calculate_ma7(prices):
    """Реальный MA7 — скользящее среднее за 7 дней"""
    if len(prices) < 7:
        return None
    return round(sum(prices[-7:]) / 7, 4)

def calculate_rsi(prices):
    """Реальный RSI на основе 7 дней"""
    if len(prices) < 8:
        return None

    gains = []
    losses = []
    for i in range(1, 8):
        delta = prices[i] - prices[i - 1]
        if delta > 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))

    avg_gain = sum(gains) / 7 if gains else 0.0001
    avg_loss = sum(losses) / 7 if losses else 0.0001

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

async def fetch_historical_prices(coin_id, days=8):
    """Получает исторические цены монеты за N дней (для RSI и MA7)"""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return [safe_float(price[1]) for price in data.get("prices", [])]
            return []

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
    """Получает данные по монетам и дополняет их RSI и MA7 (с кешем и fallback-логикой)"""
    raw_data = await fetch_all_coin_data(coin_ids)
    result = []

    for coin in raw_data:
        coin_id = coin.get("id", "")
        current_price = safe_float(coin.get("current_price"))
        change_24h = safe_float(coin.get("price_change_percentage_24h"))
        volume = safe_float(coin.get("total_volume"))

        cached = INDICATOR_CACHE.get(coin_id, {})
        timestamp = cached.get("timestamp")
        now = datetime.utcnow()
        is_fresh = timestamp and (now - datetime.fromisoformat(timestamp)) < timedelta(hours=1)

        if is_fresh:
            rsi = safe_float(cached.get("rsi"))
            ma7 = safe_float(cached.get("ma7"))
        else:
            prices = await fetch_historical_prices(coin_id)
            rsi = calculate_rsi(prices) or simulate_rsi(change_24h)
            ma7 = calculate_ma7(prices) or simulate_ma7(current_price)
            INDICATOR_CACHE[coin_id] = {
                "rsi": rsi,
                "ma7": ma7,
                "timestamp": now.isoformat()
            }

        coin["current_price"] = current_price
        coin["price_change_percentage_24h"] = change_24h
        coin["total_volume"] = volume
        coin["rsi"] = rsi
        coin["ma7"] = ma7

        result.append(coin)

    save_cache()
    return result

async def get_current_price(symbol):
    """Получает текущую цену монеты по её символу. Совместима с CoinTracker"""
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
