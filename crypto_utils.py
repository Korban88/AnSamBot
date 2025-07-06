import httpx
import logging
import random
import json
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CACHE_FILE = "indicators_cache.json"
CACHE_TTL_HOURS = 12

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка чтения кеша: {e}")
        return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        logger.error(f"Ошибка записи кеша: {e}")

def is_fresh(timestamp_str):
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        return datetime.utcnow() - timestamp < timedelta(hours=CACHE_TTL_HOURS)
    except Exception:
        return False

cache = load_cache()

def get_rsi(coin_id):
    try:
        if coin_id in cache and "rsi" in cache[coin_id] and is_fresh(cache[coin_id]["rsi"]["timestamp"]):
            return cache[coin_id]["rsi"]["value"]
        value = round(random.uniform(40, 75), 2)
        logger.debug(f"📈 RSI для {coin_id}: {value}")
        cache.setdefault(coin_id, {})["rsi"] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
        save_cache(cache)
        return value
    except Exception as e:
        logger.error(f"⚠️ Ошибка при получении RSI для {coin_id}: {e}")
        return None

def get_moving_average(coin_id):
    try:
        if coin_id in cache and "ma" in cache[coin_id] and is_fresh(cache[coin_id]["ma"]["timestamp"]):
            return cache[coin_id]["ma"]["value"]
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
        logger.debug(f"📉 MA(7d) для {coin_id}: {ma}")
        cache.setdefault(coin_id, {})["ma"] = {
            "value": ma,
            "timestamp": datetime.utcnow().isoformat()
        }
        save_cache(cache)
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
