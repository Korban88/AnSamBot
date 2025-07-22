import aiohttp
import json
import os

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

async def get_market_data(symbol):
    coin_id = SYMBOL_ID_MAP.get(symbol)
    if not coin_id:
        return None
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                market_data = data.get("market_data", {})
                return {
                    "price": market_data.get("current_price", {}).get("usd"),
                    "change_24h": market_data.get("price_change_percentage_24h"),
                    "volume": market_data.get("total_volume", {}).get("usd"),
                    "rsi": 50,  # Можно заменить на расчётный
                    "ma": market_data.get("current_price", {}).get("usd")  # заглушка MA = текущая цена
                }
    except:
        return None
