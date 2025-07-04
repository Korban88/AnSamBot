import requests
import logging
from ton_tokens import get_ton_wallet_tokens

def fetch_coin_data(coin_ids):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Ошибка при получении данных с CoinGecko: {e}")
        return {}

def estimate_growth_probability(change_24h, volume):
    if change_24h > 4 and volume > 10_000_000:
        return 80
    if change_24h > 2 and volume > 5_000_000:
        return 70
    if change_24h > 0:
        return 60
    return 50

def get_top_coins():
    coin_ids = get_ton_wallet_tokens()
    logging.info(f"Список монет из ton_tokens: {coin_ids}")

    data = fetch_coin_data(coin_ids)
    if not data:
        logging.warning("Нет данных от CoinGecko")
        return []

    coins = []
    for coin_id in coin_ids:
        if coin_id in data:
            price = data[coin_id].get("usd")
            change_24h = data[coin_id].get("usd_24h_change", 0)
            volume = 10_000_000  # временно жёстко задан, позже подставим реальные данные

            probability = estimate_growth_probability(change_24h, volume)

            if probability < 65 or change_24h < -3:
                logging.info(f"Монета {coin_id} отфильтрована: change={change_24h}, prob={probability}")
                continue

            coin = {
                "id": coin_id,
                "price": round(price, 4),
                "change_24h": round(change_24h, 2),
                "probability": probability,
                "target_price": round(price * 1.05, 4),
                "stop_loss_price": round(price * 0.965, 4)
            }
            coins.append(coin)
        else:
            logging.info(f"Нет данных по монете: {coin_id}")

    logging.info(f"Анализ завершён. Подходящих монет: {len(coins)}")
    return sorted(coins, key=lambda x: x['probability'], reverse=True)[:3]
