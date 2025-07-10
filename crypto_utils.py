import httpx
import json, time, os
from config import INDICATORS_CACHE_FILE
from crypto_list import TELEGRAM_WALLET_CRYPTOS

def load_indicators():
    if os.path.exists(INDICATORS_CACHE_FILE):
        try:
            return json.load(open(INDICATORS_CACHE_FILE))
        except:
            return {}
    return {}

def fetch_and_cache_indicators():
    indicators = {}
    batch_size = 5
    for i in range(0, len(TELEGRAM_WALLET_CRYPTOS), batch_size):
        batch = TELEGRAM_WALLET_CRYPTOS[i:i+batch_size]
        ids = ",".join(batch)
        try:
            resp = httpx.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={"vs_currency":"usd", "ids":ids, "price_change_percentage":"24h"},
                timeout=10
            )
            if resp.status_code != 200:
                print(f"⛔ HTTP {resp.status_code} for batch {batch}")
            else:
                for coin in resp.json():
                    indicators[coin["id"]] = {
                        "price": coin.get("current_price"),
                        "change_24h": coin.get("price_change_percentage_24h"),
                        "rsi": 50.0,
                        "ma": coin.get("current_price")
                    }
            time.sleep(3)
        except Exception as e:
            print("Ошибка при запросе:", e)

    json.dump(indicators, open(INDICATORS_CACHE_FILE, "w"), indent=2)
    print(f"✅ Индикаторы сохранены в {INDICATORS_CACHE_FILE}")

def get_current_price(cid):
    return load_indicators().get(cid, {}).get("price")

def get_24h_change(cid):
    return load_indicators().get(cid, {}).get("change_24h")

def get_rsi(cid):
    return load_indicators().get(cid, {}).get("rsi")

def get_ma(cid):
    return load_indicators().get(cid, {}).get("ma")
