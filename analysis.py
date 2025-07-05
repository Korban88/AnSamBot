import httpx
import logging
from crypto_list import crypto_list

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
log = logging.getLogger("analysis")

def fetch_prices():
    ids = ",".join(crypto['id'] for crypto in crypto_list)
    params = {"ids": ids, "vs_currencies": "usd"}

    try:
        response = httpx.get(COINGECKO_API_URL, params=params)
        if response.status_code != 200:
            log.warning(f"[fetch_prices] Ошибка при получении данных: {response.status_code}")
            return {}

        data = response.json()
        prices = {}

        for crypto in crypto_list:
            price_info = data.get(crypto["id"])
            if price_info:
                prices[crypto["symbol"]] = price_info.get("usd")
            else:
                log.warning(f"[fetch_prices] Нет цены для {crypto['id']} в batch-ответе")

        log.info(f"[fetch_prices] Получены цены для {len(prices)} монет.")
        return prices

    except Exception as e:
        log.error(f"[fetch_prices] Ошибка запроса: {e}")
        return {}

def analyze_prices(prices):
    analyzed = []
    for crypto in crypto_list:
        symbol = crypto["symbol"]
        price = prices.get(symbol)
        if price:
            # Временная формула вероятности
            score = 0.5 + (1 / price if price < 10 else 0.1)
            probability = min(round(score * 100, 2), 95.0)
            analyzed.append({
                "symbol": symbol.upper(),
                "price": price,
                "score": score,
                "probability": probability
            })

    log.info(f"[analyze_prices] Проанализировано {len(analyzed)} монет.")
    return analyzed

def get_top_3_cryptos():
    prices = fetch_prices()
    if not prices:
        log.warning("[get_top_3_cryptos] Нет данных о ценах.")
        return []

    analyzed = analyze_prices(prices)
    top_3 = sorted(analyzed, key=lambda x: x["probability"], reverse=True)[:3]

    log.info("[get_top_3_cryptos] Топ-3 монеты:")
    for coin in top_3:
        log.info(f" - {coin['symbol']}: {coin['probability']}% при {coin['price']} USD")

    return top_3
