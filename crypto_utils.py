# crypto_utils.py

import requests
import time
import json
import os
from config import INDICATORS_CACHE_FILE

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

HEADERS = {
    'accept': 'application/json'
}

def load_cache():
    if os.path.exists(INDICATORS_CACHE_FILE):
        with open(INDICATORS_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(INDICATORS_CACHE_FILE, "w") as f:
        json.dump(cache, f)

def get_current_price(coin_id):
    try:
        url = f"{COINGECKO_API_URL}/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd"}
        response = requests.get(url, params=params, headers=HEADERS)
        data = response.json()
        return data[coin_id]["usd"]
    except:
        return None

def get_24h_change(coin_id):
    try:
        url = f"{COINGECKO_API_URL}/coins/{coin_id}"
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        return data["market_data"]["price_change_percentage_24h"]
    except:
        return None

def get_rsi(coin_id):
    cache = load_cache()
    now = int(time.time())
    if coin_id in cache and "rsi" in cache[coin_id]:
        if now - cache[coin_id]["rsi"]["timestamp"] < 3600:  # 1 час кеш
            return cache[coin_id]["rsi"]["value"]

    try:
        url = f"https://api.taapi.io/rsi"
        params = {
            "secret": "demo",  # заменим позже при необходимости
            "exchange": "binance",
            "symbol": f"{coin_id.upper()}/USDT",
            "interval": "1h"
        }
        response = requests.get(url, params=params)
        data = response.json()
        rsi = float(data["value"])

        if coin_id not in cache:
            cache[coin_id] = {}
        cache[coin_id]["rsi"] = {"value": rsi, "timestamp": now}
        save_cache(cache)

        return rsi
    except:
        return None

def get_ma(coin_id):
    cache = load_cache()
    now = int(time.time())
    if coin_id in cache and "ma" in cache[coin_id]:
        if now - cache[coin_id]["ma"]["timestamp"] < 3600:  # 1 час кеш
            return cache[coin_id]["ma"]["value"]

    try:
        url = f"https://api.taapi.io/ma"
        params = {
            "secret": "demo",  # заменим позже при необходимости
            "exchange": "binance",
            "symbol": f"{coin_id.upper()}/USDT",
            "interval": "1h"
        }
        response = requests.get(url, params=params)
        data = response.json()
        ma = float(data["value"])

        if coin_id not in cache:
            cache[coin_id] = {}
        cache[coin_id]["ma"] = {"value": ma, "timestamp": now}
        save_cache(cache)

        return ma
    except:
        return None
