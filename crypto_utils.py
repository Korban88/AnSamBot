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
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def simulate_rsi(price_change):
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

def simulate_ma(price, days=7):
    import random
    variation = random.uniform(-0.03, 0.03)
    return round(safe_float(price) * (1 - variation), 4)

def calculate_ma(prices, days=7):
    if len(prices) < days:
        return None
    return round(sum(prices[-days:]) / days, 4)

def calculate_rsi(prices):
    if len(prices) < 8:
        return None

    gains, losses = [], []
    for i in range(1, 8):
        delta = prices[i] - prices[i - 1]
        if delta > 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))

    avg_gain = sum(gains) / 7 if gains else 0.0001
    avg_loss = sum(losses) / 7 if losses else 0.0001

    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

async def fetch_historical_prices(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return [safe_float(price[1]) for price in data.get("prices", [])]
            return []

async def fetch_all_coin_data(coin_ids):
    """Получает данные с CoinGecko чанками по 45 монет"""
    results = []
    chunk_size = 45
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(coin_ids), chunk_size):
            chunk = coin_ids[i:i + chunk_size]
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "ids": ",".join(chunk),
                "price_change_percentage": "24h,7d"
            }
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results.extend(data)
                else:
                    print(f"⚠️ Ошибка API {response.status} для монет: {chunk}")
    return results

async def get_all_coin_data(coin_ids):
    raw_data = await fetch_all_coin_data(coin_ids)
    result = []

    for coin in raw_data:
        coin_id = coin.get("id", "")
        current_price = safe_float(coin.get("current_price"))
        change_24h = safe_float(coin.get("price_change_percentage_24h"))
        change_7d = safe_float(coin.get("price_change_percentage_7d_in_currency"))
        volume = safe_float(coin.get("total_volume"))

        cached = INDICATOR_CACHE.get(coin_id, {})
        timestamp = cached.get("timestamp")
        now = datetime.utcnow()
        is_fresh = timestamp and (now - datetime.fromisoformat(timestamp)) < timedelta(hours=1)

        if is_fresh:
            rsi = safe_float(cached.get("rsi"))
            ma7 = safe_float(cached.get("ma7"))
            ma30 = safe_float(cached.get("ma30"))
        else:
            prices = await fetch_historical_prices(coin_id, days=30)
            rsi = calculate_rsi(prices[-8:]) or simulate_rsi(change_24h)
            ma7 = calculate_ma(prices, days=7) or simulate_ma(current_price, days=7)
            ma30 = calculate_ma(prices, days=30) or simulate_ma(current_price, days=30)
            INDICATOR_CACHE[coin_id] = {
                "rsi": rsi,
                "ma7": ma7,
                "ma30": ma30,
                "timestamp": now.isoformat()
            }

        coin["current_price"] = current_price
        coin["price_change_percentage_24h"] = change_24h
        coin["price_change_percentage_7d"] = change_7d
        coin["total_volume"] = volume
        coin["rsi"] = rsi
        coin["ma7"] = ma7
        coin["ma30"] = ma30

        result.append(coin)

    save_cache()
    return result

async def get_current_price(symbol):
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
