import requests
import logging

logger = logging.getLogger(__name__)

COINGECKO_API = "https://api.coingecko.com/api/v3"

DEFAULT_COINS = [
    "bitcoin", "ethereum", "toncoin", "solana", "cardano", "dogecoin",
    "ripple", "polkadot", "avalanche-2", "shiba-inu", "chainlink",
    "litecoin", "uniswap", "stellar", "algorand", "monero", "aptos",
    "near", "cosmos", "the-graph", "tezos", "aave", "hedera", "filecoin", "maker"
]

def get_top_coins():
    try:
        response = requests.get(f"{COINGECKO_API}/coins/markets", params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 25,
            "page": 1,
            "sparkline": "false"
        })
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка при получении списка монет: {e}")
        return []

def get_coin_price(symbol):
    try:
        response = requests.get(f"{COINGECKO_API}/simple/price", params={
            "ids": symbol,
            "vs_currencies": "usd"
        })
        response.raise_for_status()
        return response.json().get(symbol, {}).get("usd")
    except Exception as e:
        logger.error(f"Ошибка при получении цены для {symbol}: {e}")
        return None

def get_price_by_symbol(symbol):
    """
    Получает актуальную цену монеты по её символу (например, 'btc' или 'toncoin')
    """
    coins = get_top_coins()
    for coin in coins:
        if coin['symbol'].lower() == symbol.lower():
            return coin['current_price']
    return None
