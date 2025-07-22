import aiohttp
import json
import os
from datetime import datetime, timedelta
from statistics import mean

INDICATOR_CACHE_FILE = "indicators_cache.json"

SYMBOL_ID_MAP = {
    "TON": "the-open-network", "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
    "TRX": "tron", "USDT": "tether", "USDC": "usd-coin", "DAI": "dai", "BUSD": "binance-usd",
    "WBTC": "wrapped-bitcoin", "LTC": "litecoin", "MATIC": "matic-network", "DOGE": "dogecoin",
    "SHIB": "shiba-inu", "AVAX": "avalanche-2", "LINK": "chainlink", "UNI": "uniswap",
    "XRP": "ripple", "XLM": "stellar", "DOT": "polkadot", "SOL": "solana", "NEAR": "near",
    "ADA": "cardano", "ETC": "ethereum-classic", "ATOM": "cosmos", "EOS": "eos", "XTZ": "tezos",
    "AAVE": "aave", "APE": "apecoin", "SAND": "the-sandbox", "MANA": "decentraland", "DYDX": "dydx",
    "CAKE": "pancakeswap-token", "CHZ": "chiliz", "ZRX": "0x", "1INCH": "1inch",
    "COMP": "compound-governance-token", "CRV": "curve-dao-token", "RUNE": "thorchain",
    "SNX": "synthetix-network-token", "GRT": "the-graph", "BAT": "basic-attention-token",
    "ENJ": "enjincoin", "REN": "republic-protocol", "YFI": "yearn-finance", "BAL": "balancer",
    "TWT": "trust-wallet-token", "LDO": "lido-dao", "GMX": "gmx", "AR": "arweave",
    "OP": "optimism", "RNDR": "render-token"
}

def load_indicator_cache():
    if os.path.exists(INDICATOR_CACHE_FILE):
        with open(INDICATOR_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_indicator_cache(cache):
    with open(INDICATOR_CACHE_FILE, "w") as f:
        json.dump(cache, f)

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    deltas = [prices[i+1] - prices[i] for i in range(len(prices) - 1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = mean(gains[-period:]) if gains else 0
    avg_loss = mean(losses[-period:]) if losses else 0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calculate_volatility(prices):
    if not prices or len(prices) < 2:
        return 0
    return round((max(prices) - min(prices)) / mean(prices) * 100, 2)

def volume_growth(volumes):
    if len(volumes) < 2 or volumes[-2] == 0:
        return 0
    return round((volumes[-1] - volumes[-2]) / volumes[-2] * 100, 2)

async def get_market_data(symbol):
    coin_id = SYMBOL_ID_MAP.get(symbol)
    if not coin_id:
        return None

    cache = load_indicator_cache()
    now = datetime.utcnow().isoformat()
    if symbol in cache and "timestamp" in cache[symbol]:
        cached_time = datetime.fromisoformat(cache[symbol]["timestamp"])
        if datetime.utcnow() - cached_time < timedelta(hours=1):
            return cache[symbol]["data"]

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=2&interval=hourly"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                chart = await resp.json()
                prices = [p[1] for p in chart.get("prices", [])]
                volumes = [v[1] for v in chart.get("total_volumes", [])]
                if not prices or not volumes or len(prices) < 24:
                    return None

                rsi = calculate_rsi(prices[-20:])
                volat = calculate_volatility(prices[-24:])
                vol_growth = volume_growth(volumes[-24:])
    except Exception as e:
        print(f"Ошибка данных {symbol}: {e}")
        return None

    # текущие данные
    market_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(market_url) as resp:
                data = await resp.json()
                m = data.get("market_data", {})
                result = {
                    "price": m.get("current_price", {}).get("usd"),
                    "change_24h": m.get("price_change_percentage_24h"),
                    "volume_24h": m.get("total_volume", {}).get("usd"),
                    "rsi": rsi,
                    "volatility": volat,
                    "volume_growth": vol_growth
                }
                # кешируем
                cache[symbol] = {
                    "timestamp": now,
                    "data": result
                }
                save_indicator_cache(cache)
                return result
    except:
        return None

# 🔁 Нужно для tracking.py
async def get_price(symbol):
    coin_id = SYMBOL_ID_MAP.get(symbol)
    if not coin_id:
        return None
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data.get(coin_id, {}).get("usd")
    except:
        return None
