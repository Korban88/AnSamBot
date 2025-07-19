import requests
import json
import os
import time

INDICATOR_CACHE_FILE = "indicators_cache.json"

SYMBOL_ID_MAP = {
    "TON": "the-open-network",
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "TRX": "tron",
    "USDT": "tether",
    "USDC": "usd-coin",
    "DAI": "dai",
    "BUSD": "binance-usd",
    "WBTC": "wrapped-bitcoin",
    "LTC": "litecoin",
    "MATIC": "matic-network",
    "DOGE": "dogecoin",
    "SHIB": "shiba-inu",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "XRP": "ripple",
    "XLM": "stellar",
    "DOT": "polkadot",
    "SOL": "solana",
    "NEAR": "near",
    "ADA": "cardano",
    "ETC": "ethereum-classic",
    "ATOM": "cosmos",
    "EOS": "eos",
    "XTZ": "tezos",
    "AAVE": "aave",
    "APE": "apecoin",
    "SAND": "the-sandbox",
    "MANA": "decentraland",
    "DYDX": "dydx",
    "CAKE": "pancakeswap-token",
    "CHZ": "chiliz",
    "ZRX": "0x",
    "1INCH": "1inch",
    "COMP": "compound-governance-token",
    "CRV": "curve-dao-token",
    "RUNE": "thorchain",
    "SNX": "synthetix-network-token",
    "GRT": "the-graph",
    "BAT": "basic-attention-token",
    "ENJ": "enjincoin",
    "REN": "republic-protocol",
    "YFI": "yearn-finance",
    "BAL": "balancer",
    "TWT": "trust-wallet-token",
    "LDO": "lido-dao",
    "GMX": "gmx",
    "AR": "arweave",
    "OP": "optimism",
    "RNDR": "render-token"
}

def load_indicator_cache():
    if os.path.exists(INDICATOR_CACHE_FILE):
        with open(INDICATOR_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_indicator_cache(cache):
    with open(INDICATOR_CACHE_FILE, "w") as f:
        json.dump(cache, f)

def get_price(symbol):
    coin_id = SYMBOL_ID_MAP.get(symbol)
    if not coin_id:
        return None
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()[coin_id]["usd"]
    except Exception:
        return None

def get_market_data(symbol):
    coin_id = SYMBOL_ID_MAP.get(symbol)
    if not coin_id:
        return None
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        market_data = data.get("market_data", {})
        return {
            "price": market_data.get("current_price", {}).get("usd"),
            "change_24h": market_data.get("price_change_percentage_24h"),
            "volume": market_data.get("total_volume", {}).get("usd"),
            "rsi": calculate_rsi_placeholder(symbol),  # заглушка, будет заменена реальным RSI
            "ma": calculate_ma_placeholder(symbol),    # заглушка, будет заменена реальным MA
        }
    except Exception:
        return None

def calculate_rsi_placeholder(symbol):
    return 50  # тут позже будет кэшированный RSI

def calculate_ma_placeholder(symbol):
    return 50  # тут позже будет кэшированный MA

def reset_cache():
    if os.path.exists(INDICATOR_CACHE_FILE):
        os.remove(INDICATOR_CACHE_FILE)
