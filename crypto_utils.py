import requests

# Используется в анализе и генерации сигналов
def get_top_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "volume_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h"
    }
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Ошибка при получении топ-коинов: {e}")
        return []

# Получение текущей цены по символу
def get_price(symbol):
    try:
        coins = get_top_coins()
        for coin in coins:
            if coin["symbol"].lower() == symbol.lower():
                return coin["current_price"]
        return None
    except Exception as e:
        print(f"Ошибка при получении цены {symbol}: {e}")
        return None
