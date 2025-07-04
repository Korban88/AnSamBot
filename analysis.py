import requests
import datetime
import time
import logging

from crypto_list import crypto_list


def get_current_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data[symbol]["usd"]
    except Exception as e:
        logging.warning(f"Ошибка получения цены для {symbol}: {e}")
        return None


def get_price_history(symbol, days=1):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days={days}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if 'prices' in data:
            return data['prices']
        else:
            raise ValueError(f"'prices' не найден в данных для {symbol}")
    except Exception as e:
        logging.warning(f"Ошибка анализа {symbol}: {e}")
        return None


def analyze_coin(symbol):
    prices = get_price_history(symbol)
    if not prices or len(prices) < 2:
        return None

    current_price = prices[-1][1]
    previous_price = prices[0][1]
    change_percent = ((current_price - previous_price) / previous_price) * 100

    # Фиктивная логика оценки (заменим позже на реальную)
    score = max(0, min(100, 50 + change_percent))  # просто как заглушка
    probability = round(min(100, max(0, 50 + change_percent)), 2)

    return {
        "symbol": symbol,
        "current_price": round(current_price, 6),
        "change_percent": round(change_percent, 2),
        "probability": probability,
        "score": score,
    }


def analyze_all_coins():
    results = []
    for symbol in crypto_list:
        time.sleep(1.3)  # защита от блокировки API
        result = analyze_coin(symbol)
        if result and result["probability"] >= 65 and result["change_percent"] > -3:
            results.append(result)

    results.sort(key=lambda x: x["probability"], reverse=True)
    return results[:3]  # только топ-3
