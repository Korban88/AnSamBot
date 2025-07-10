import httpx
import json
import time
import os
from config import INDICATORS_CACHE_FILE
from crypto_list import TELEGRAM_WALLET_CRYPTOS

def load_indicators():
    if os.path.exists(INDICATORS_CACHE_FILE):
        with open(INDICATORS_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def get_current_price(coin_id):
    indicators = load_indicators()
    return indicators.get(coin_id, {}).get("price")

def get_24h_change(coin_id):
    indicators = load_indicators()
    return indicators.get(coin_id, {}).get("change_24h")

def get_rsi(coin_id):
    indicators = load_indicators()
    return indicators.get(coin_id, {}).get("rsi")

def get_ma(coin_id):
    indicators = load_indicators()
    return indicators.get(coin_id, {}).get("ma")

def fetch_and_cache_indicators():
    indicators = {}

    batch_size = 10
    for i in range(0, len(TELEGRAM_WALLET_CRYPTOS), batch_size):
        batch = TELEGRAM_WALLET_CRYPTOS[i:i + batch_size]
        ids = ",".join(batch)

        try:
            url = f"https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "ids": ids,
                "price_change_percentage": "24h"
            }
            response = httpx.get(url, params=params, timeout=10)

            if response.status_code != 200:
                print(f"Ошибка статуса: {response.status_code}")
                continue

            data = response.json()
            for coin in data:
                indicators[coin["id"]] = {
                    "price": coin.get("current_price"),
                    "change_24h": coin.get("price_change_percentage_24h"),
                    "rsi": 50.0,  # заглушка
                    "ma": coin.get("current_price"),  # заглушка
                }

            time.sleep(1)  # анти-429

        except Exception as e:
            print(f"Ошибка при получении данных: {e}")

    with open(INDICATORS_CACHE_FILE, "w") as f:
        json.dump(indicators, f, indent=2)

    print(f"✅ Индикаторы сохранены в {INDICATORS_CACHE_FILE}")
