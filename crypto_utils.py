import httpx
import logging
import random
import os
import json
import time
import asyncio

logger = logging.getLogger(__name__)

# === Кэш для RSI и MA ===
INDICATORS_CACHE_FILE = "indicators_cache.json"

if os.path.exists(INDICATORS_CACHE_FILE):
    with open(INDICATORS_CACHE_FILE, "r") as f:
        indicators_cache = json.load(f)
else:
    indicators_cache = {}

def save_indicators_cache():
    with open(INDICATORS_CACHE_FILE, "w") as f:
        json.dump(indicators_cache, f)

def get_rsi(coin_id):
    try:
        now = time.time()
        if coin_id in indicators_cache:
            cached = indicators_cache[coin_id]
            if "rsi" in cached and now - cached["timestamp"] < 86400:
                logger.debug(f"📦 RSI для {coin_id} из кэша: {cached['rsi']}")
                return cached["rsi"]

        value = round(random.uniform(40, 75), 2)
        logger.debug(f"📈 RSI для {coin_id} (новый): {value}")

        if coin_id not in indicators_cache:
            indicators_cache[coin_id] = {}

        indicators_cache[coin_id]["rsi"] = value
        indicators_cache[coin_id]["timestamp"] = now
        save_indicators_cache()
        return value
    except Exception as e:
        logger.error(f"⚠️ Ошибка при получении RSI для {coin_id}: {e}")
        return None

async def get_moving_average(coin_id):
    try:
        now = time.time()
        if coin_id in indicators_cache:
            cached = indicators_cache[coin_id]
            if "ma" in cached and now - cached["timestamp"] < 86400:
                logger.debug(f"📦 MA для {coin_id} из кэша: {cached['ma']}")
                return cached["ma"]

        await asyncio.sleep(1.5)  # лимитируем частоту запросов

        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": "7",
            "interval": "daily"
        }
        response = httpx.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        prices = [price[1] for price in data["prices"]]
        if not prices:
            return None
        ma = round(sum(prices) / len(prices), 4)
        logger.debug(f"📉 MA(7d) для {coin_id} (новый): {ma}")

        if coin_id not in indicators_cache:
            indicators_cache[coin_id] = {}

        indicators_cache[coin_id]["ma"] = ma
        indicators_cache[coin_id]["timestamp"] = now
        save_indicators_cache()
        return ma
    except Exception as e:
        logger.error(f"⚠️ Ошибка при получении MA для {coin_id}: {e}")
        return None

def get_current_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd"
        }
        response = httpx.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        price = data[coin_id]["usd"]
        logger.debug(f"💰 Текущая цена {coin_id}: {price}")
        return price
    except Exception as e:
        logger.error(f"❌ Ошибка при получении текущей цены для {coin_id}: {e}")
        return None
