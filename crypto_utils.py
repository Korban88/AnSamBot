import requests

COINGECKO_URL = "https://api.coingecko.com/api/v3"

def get_top_coins(limit=20):
    response = requests.get(f"{COINGECKO_URL}/coins/markets", params={
        "vs_currency": "usd",
        "order": "volume_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False
    })
    return response.json() if response.status_code == 200 else []

def get_price_by_symbol(symbol):
    coins = get_top_coins(100)
    for coin in coins:
        if coin["symbol"].lower() == symbol.lower():
            return coin["current_price"]
    return None

def get_current_price(symbol):
    coins = get_top_coins(100)
    for coin in coins:
        if coin["symbol"].lower() == symbol.lower():
            return coin["current_price"]
    return None
