import requests
import random
import logging

def analyze_coin(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": 7,
            "interval": "hourly"
        }
        response = requests.get(url, params=params)
        data = response.json()

        prices = [price[1] for price in data["prices"]]
        if len(prices) < 20:
            return None

        # RSI (простая модель)
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]
        avg_gain = sum(gains[-14:]) / 14 if gains else 0.01
        avg_loss = sum(losses[-14:]) / 14 if losses else 0.01
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Скользящие средние
        ma7 = sum(prices[-7:]) / 7
        ma20 = sum(prices[-20:]) / 20

        # Изменение за 24 часа
        change_24h = ((prices[-1] - prices[-25]) / prices[-25]) * 100

        # Условная формула "оценки"
        score = (
            (rsi - 50) * 0.4 +
            ((ma7 - ma20) / ma20) * 100 * 0.4 +
            change_24h * 0.2
        )

        # Перевод оценки в вероятность
        probability = min(100, max(0, round(60 + score * 0.8, 2)))

        logging.info(f"[Анализ] {coin_id}: prob={probability}%, vol={prices[-1] * 1000000:.2f}, 24h={change_24h}%")

        return {
            "rsi": round(rsi, 2),
            "ma7": round(ma7, 4),
            "ma20": round(ma20, 4),
            "score": round(score, 2),
            "probability": probability,
        }

    except Exception as e:
        logging.warning(f"Ошибка анализа {coin_id}: {e}")
        return None
