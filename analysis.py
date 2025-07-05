import logging
import requests
from crypto_list import crypto_list

logger = logging.getLogger(__name__)

def get_price(coin):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        response = requests.get(url)
        return response.json().get(coin, {}).get("usd")
    except Exception as e:
        logger.warning(f"Ошибка при получении цены для {coin}: {e}")
        return None

def analyze_coin(coin):
    price = get_price(coin)
    if price is None:
        return None

    # Простейший анализ (для примера): считаем, что монета перспективна, если цена > 0.1
    score = 1 if price > 0.1 else 0
    probability = 75 if score == 1 else 40

    return {
        "coin": coin,
        "price": price,
        "score": score,
        "probability": probability,
        "entry": round(price, 4),
        "target": round(price * 1.05, 4),
        "stop": round(price * 0.97, 4),
    }

def get_top_signals():
    signals = []
    for coin in crypto_list:
        result = analyze_coin(coin)
        if result and result["probability"] >= 65:
            signals.append(result)

    signals.sort(key=lambda x: x["probability"], reverse=True)
    return signals[:3]  # топ-3 сигнала
