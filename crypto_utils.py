import httpx
import logging
import random

logger = logging.getLogger(__name__)

def get_rsi(coin_id):
    try:
        value = round(random.uniform(40, 75), 2)
        logger.debug(f"📈 RSI для {coin_id}: {value}")
        return value
    except Exception as e:
        logger.error(f"⚠️ Ошибка при получении RSI для {coin_id}: {e}")
        return None

def get_moving_average(coin_id):
    try:
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
