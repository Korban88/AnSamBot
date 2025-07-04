import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_price_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": "1",
        "interval": "hourly"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()

        if 'prices' not in data:
            logger.warning(f"Данные по монете '{coin_id}' не содержат 'prices'. Ответ API: {data}")
            return None

        return data['prices']
    except Exception as e:
        logger.error(f"Ошибка при получении данных для {coin_id}: {e}")
        return None

def analyze_coin(coin_id):
    prices = get_price_data(coin_id)
    if not prices:
        return None

    start_price = prices[0][1]
    end_price = prices[-1][1]
    change_pct = ((end_price - start_price) / start_price) * 100

    score = max(0, min(100, change_pct + 50))  # Условная формула оценки
    probability = min(100, max(0, round(50 + (change_pct * 1.5), 2)))  # Вероятность как функция от роста

    return {
        "coin_id": coin_id,
        "start_price": round(start_price, 4),
        "end_price": round(end_price, 4),
        "change_pct": round(change_pct, 2),
        "score": round(score, 2),
        "probability": probability
    }
