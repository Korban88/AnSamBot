import httpx
import json
import os
import time
from config import INDICATORS_CACHE_FILE
from crypto_list import TELEGRAM_WALLET_CRYPTOS


def load_indicators():
    if os.path.exists(INDICATORS_CACHE_FILE):
        with open(INDICATORS_CACHE_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def fetch_and_cache_indicators():
    indicators = {}
    batch_size = 10
    for i in range(0, len(TELEGRAM_WALLET_CRYPTOS), batch_size):
        batch = TELEGRAM_WALLET_CRYPTOS[i:i + batch_size]
        ids = ",".join(batch)

        try:
            response = httpx.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": ids,
                    "price_change_percentage": "24h"
                },
                timeout=10
            )
            if response.status_code != 200:
                print(f"Ошибка статуса: {response.status_code}")
                continue

            data = response.json()
            for coin in data:
                indicators[coin["id"]] = {
                    "price": coin.get("current_price"),
                    "change_24h": coin.get("price_change_percentage_24h"),
                    "rsi": 50.0,
                    "ma": coin.get("current_price"),
                }
            time.sleep(1)
        except Exception as e:
            print(f"Ошибка при получении данных: {e}")

    with open(INDICATORS_CACHE_FILE, "w") as f:
        json.dump(indicators, f, indent=2)

    print(f"✅ Индикаторы сохранены в {INDICATORS_CACHE_FILE}")
