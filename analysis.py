import httpx
import logging
from crypto_list import crypto_list

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
log = logging.getLogger("analysis")

def fetch_prices():
    ids = ",".join(crypto['id'] for crypto in crypto_list)
    params = {"ids": ids, "vs_currencies": "usd"}
    try:
        response = httpx.get(COINGECKO_API_URL, params=params, timeout=10)
        response.raise_for_status()
    except Exception as e:
        log.warning(f"Ошибка при получении данных: {e}")
        return {}

    data = response.json()
    prices = {}

    for crypto in crypto_list:
        price_info = data.get(crypto["id"])
        if price_info:
            prices[crypto["symbol"]] = price_info.get("usd")
        else:
            log.warning(f"Нет цены для {crypto['id']} в batch-ответе.")
    return prices

def analyze_prices(prices):
    analyzed = []
    for crypto in crypto_list:
        symbol = crypto["symbol"]
        price = prices.get(symbol)
        if price:
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
    if not prices:
        return []

    analyzed = analyze_prices(prices)
    top_3 = sorted(analyzed, key=lambda x: x["probability"], reverse=True)[:3]
    return top_3
