import httpx
import logging
from crypto_list import crypto_list

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
log = logging.getLogger("analysis")

def fetch_prices():
    ids = ",".join(crypto['id'] for crypto in crypto_list)
    params = {"ids": ids, "vs_currencies": "usd"}
    response = httpx.get(COINGECKO_API_URL, params=params)

    if response.status_code != 200:
        log.warning(f"Ошибка при получении данных: {response.status_code}")
        return {}

    data = response.json()
    prices = {}

    for crypto in crypto_list:
        price_info = data.get(crypto["id"])
        if price_info:
            prices[crypto["symbol"]] = price_info.get("usd")
        else:
            log.warning(f"Нет цены для {crypto['id']} в batch-ответе: {price_info}")
    return prices

def analyze_prices(prices):
    analyzed = []
    for crypto in crypto_list:
        symbol = crypto["symbol"]
        price = prices.get(symbol)
        if price:
            # Временная формула вероятности, позже будет заменена на глубокий анализ
            score = 0.5 + (1 / price if price < 10 else 0.1)
            probability = min(round(score * 100, 2), 95.0)
            analyzed.append({
                "symbol": symbol.upper(),
                "price": price,
                "score": score,
                "probability": probability
            })
    return analyzed

def get_top_3_cryptos():
    prices = fetch_prices()
    analyzed = analyze_prices(prices)
    top_3 = sorted(analyzed, key=lambda x: x["probability"], reverse=True)[:3]
    return top_3
