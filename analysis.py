import requests
import logging

logger = logging.getLogger(__name__)

def get_batch_prices(coin_list):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(coin_list),
        "vs_currencies": "usd"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()

        return data
    except Exception as e:
        logger.error(f"Ошибка при получении цен: {e}")
        return {}

def analyze_all_coins(coin_list):
    results = []
    prices = get_batch_prices(coin_list)

    for coin_id in coin_list:
        if coin_id not in prices or "usd" not in prices[coin_id]:
            logger.warning(f"Нет цены для {coin_id} в batch-ответе: {prices.get(coin_id)}")
            continue

        price = prices[coin_id]["usd"]

        # Упрощённая формула вероятности
        # Позже добавим: RSI, объём, волатильность, MA и т.д.
        score = 70  # Заглушка: считаем, что монета выглядит неплохо
        probability = 65  # Пока ставим минимально допустимую вероятность

        results.append({
            "coin_id": coin_id,
            "start_price": round(price, 4),
            "end_price": round(price, 4),
            "change_pct": 0.0,
            "score": score,
            "probability": probability
        })

    return results

def get_current_price(coin_id):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coin_id,
        "vs_currencies": "usd"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data[coin_id]["usd"]
    except Exception as e:
        logger.error(f"Ошибка получения текущей цены для {coin_id}: {e}")
        return None
