import httpx
import logging
import json
import os
from config import INDICATOR_CACHE_FILE

logger = logging.getLogger(__name__)

def load_indicators_cache():
    if os.path.exists(INDICATOR_CACHE_FILE):
        try:
            with open(INDICATOR_CACHE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("⚠️ Ошибка при чтении indicators_cache.json. Используется пустой кэш.")
    return {}

def save_indicators_cache(cache):
    with open(INDICATOR_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=4)

indicators_cache = load_indicators_cache()

async def get_current_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json().get(coin_id, {}).get("usd")
    except httpx.HTTPError as e:
        logger.error(f"⚠️ Ошибка при получении цены {coin_id}: {e}")
        return None

async def get_rsi(coin_id):
    if coin_id in indicators_cache and "rsi" in indicators_cache[coin_id]:
        return indicators_cache[coin_id]["rsi"]

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=14&interval=daily"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            prices = [price[1] for price in data["prices"]]
            if len(prices) < 15:
                return None
            deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
            gains = [delta for delta in deltas if delta > 0]
            losses = [-delta for delta in deltas if delta < 0]
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 1
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            indicators_cache.setdefault(coin_id, {})["rsi"] = rsi
            save_indicators_cache(indicators_cache)
            return rsi
    except httpx.HTTPError as e:
        logger.error(f"⚠️ Ошибка при получении RSI для {coin_id}: {e}")
        return None

async def get_moving_average(coin_id):
    if coin_id in indicators_cache and "ma" in indicators_cache[coin_id]:
        return indicators_cache[coin_id]["ma"]

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7&interval=daily"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            prices = [price[1] for price in data["prices"]]
            if not prices:
                return None
            ma = sum(prices) / len(prices)
            indicators_cache.setdefault(coin_id, {})["ma"] = ma
            save_indicators_cache(indicators_cache)
            return ma
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.error(f"⚠️ Ошибка 429 при получении MA для {coin_id}: {e}")
        else:
            logger.error(f"⚠️ Ошибка при получении MA для {coin_id}: {e}")
        return None
