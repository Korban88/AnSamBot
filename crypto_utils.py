# crypto_utils.py

import httpx
import time
import json
from config import INDICATORS_CACHE_FILE

BASE_URL = "https://api.coingecko.com/api/v3"
HEADERS = {"accept": "application/json"}

# Загружаем кэш или создаем пустой
try:
    with open(INDICATORS_CACHE_FILE, "r") as f:
        indicators_cache = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    indicators_cache = {}

def save_cache():
    with open(INDICATORS_CACHE_FILE, "w") as f:
        json.dump(indicators_cache, f)

def fetch_market_data(coin_id):
    url = f"{BASE_URL}/coins/markets"
    params = {"vs_currency": "usd", "ids": coin_id, "price_change_percentage": "24h"}
    try:
        response = httpx.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None
    except httpx.HTTPStatusError as e:
        print(f"HTTP error for {coin_id}: {e.response.status_code}")
    except Exception as e:
        print(f"Error fetching market data for {coin_id}: {e}")
    return None

def fetch_rsi_ma(coin_id):
    # Простейшая заглушка вместо настоящего RSI и MA
    # При желании можно подключить TA API или TradingView
    return round(30 + hash(coin_id) % 40, 2), round(1 + (hash(coin_id[::-1]) % 500) / 100, 2)

def get_current_price(coin_id):
    if coin_id in indicators_cache and "price" in indicators_cache[coin_id]:
        return indicators_cache[coin_id]["price"]

    data = fetch_market_data(coin_id)
    if not data:
        return None

    price = data.get("current_price")
    indicators_cache.setdefault(coin_id, {})["price"] = price
    save_cache()
    return price

def get_24h_change(coin_id):
    if coin_id in indicators_cache and "change_24h" in indicators_cache[coin_id]:
        return indicators_cache[coin_id]["change_24h"]

    data = fetch_market_data(coin_id)
    if not data:
        return None

    change = data.get("price_change_percentage_24h")
    indicators_cache.setdefault(coin_id, {})["change_24h"] = change
    save_cache()
    return change

def get_rsi(coin_id):
    if coin_id in indicators_cache and "rsi" in indicators_cache[coin_id]:
        return indicators_cache[coin_id]["rsi"]

    rsi, _ = fetch_rsi_ma(coin_id)
    indicators_cache.setdefault(coin_id, {})["rsi"] = rsi
    save_cache()
    return rsi

def get_ma(coin_id):
    if coin_id in indicators_cache and "ma" in indicators_cache[coin_id]:
        return indicators_cache[coin_id]["ma"]

    _, ma = fetch_rsi_ma(coin_id)
    indicators_cache.setdefault(coin_id, {})["ma"] = ma
    save_cache()
    return ma
