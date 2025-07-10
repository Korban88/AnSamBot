# crypto_utils.py

import json
import os
from config import INDICATORS_CACHE_FILE

def load_indicators_cache():
    if os.path.exists(INDICATORS_CACHE_FILE):
        with open(INDICATORS_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def get_from_cache(coin_id, field):
    cache = load_indicators_cache()
    coin_data = cache.get(coin_id)
    if coin_data and field in coin_data:
        return coin_data[field]
    return None

def get_current_price(coin_id):
    return get_from_cache(coin_id, "price")

def get_24h_change(coin_id):
    return get_from_cache(coin_id, "change_24h")

def get_rsi(coin_id):
    return get_from_cache(coin_id, "rsi")

def get_ma(coin_id):
    return get_from_cache(coin_id, "ma")
