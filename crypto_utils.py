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

    batch_size = 30
    for i in range(0, len(TELEGRAM_WALLET_CRYPTOS), batch_size):
        batch = TELEGRAM_WALLET_CRYPTOS[i:i + batch_size]
        ids = ",".join(batch)

        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": ids,
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
            response = httpx.get(url, params=params, timeout=10)

            if response.status_code != 200:
                print(f"Ошибка статуса: {response.status_code}")
                continue

            data = response.json()

            for coin_id in batch:
                coin_data = data.get(coin_id)
                if coin_data:
                    indicators[coin_id] = {
                        "price": coin_data.get("usd"),
                        "change_24h": coin_data.get("usd_24h_change"),
                        "rsi": 50.0,  # Заглушка
                        "ma": coin_data.get("usd"),  # Заглушка
                    }
                else:
                    print(f"🔴 {coin_id} — нет данных в ответе CoinGecko")

            time.sleep(1)  # Анти-спам защита

        except Exception as e:
            print(f"❌ Ошибка при получении данных: {e}")

    with open(INDICATORS_CACHE_FILE, "w") as f:
        json.dump(indicators, f, indent=2)

    print(f"✅ Индикаторы сохранены в {INDICATORS_CACHE_FILE}")
