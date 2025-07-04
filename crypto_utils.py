import requests
import logging
import time
import statistics

logger = logging.getLogger(__name__)

def get_current_price(symbol):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": symbol,
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data[symbol]["usd"], data[symbol].get("usd_24h_change", 0)
    except Exception as e:
        logger.warning(f"Ошибка получения цены {symbol}: {e}")
        return None, None

def get_price_history(symbol, days=1):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if "prices" not in data:
            logger.warning(f"⚠️ В ответе нет 'prices' для {symbol}. Ответ: {data}")
            return []

        return [price[1] for price in data["prices"]]
    except Exception as e:
        logger.warning(f"Ошибка анализа {symbol}: {e}")
        return []

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50  # Нейтрально

    gains, losses = [], []
    for i in range(1, period + 1):
        delta = prices[-i] - prices[-i - 1]
        if delta > 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))

    average_gain = sum(gains) / period if gains else 0.001
    average_loss = sum(losses) / period if losses else 0.001

    rs = average_gain / average_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def moving_average(prices, period):
    if len(prices) < period:
        return sum(prices) / len(prices)
    return sum(prices[-period:]) / period
