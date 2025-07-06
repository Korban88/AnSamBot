import aiohttp
from indicators_cache import load_indicators_cache, save_indicators_cache
from config import TELEGRAM_WALLET_COINS

indicators_cache = load_indicators_cache()

async def get_coin_market_chart(coin_id):
    if coin_id in indicators_cache:
        return indicators_cache[coin_id]

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            indicators_cache[coin_id] = data
            save_indicators_cache(indicators_cache)
            return data

def get_rsi(coin_data, period=14):
    prices = [p[1] for p in coin_data["market_data"]["sparkline_7d"]["price"]]
    if len(prices) < period + 1:
        return 50.0

    deltas = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
    gains = [delta for delta in deltas if delta > 0]
    losses = [-delta for delta in deltas if delta < 0]

    avg_gain = sum(gains[-period:]) / period if gains[-period:] else 0.001
    avg_loss = sum(losses[-period:]) / period if losses[-period:] else 0.001

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def get_moving_average(coin_data, period=7):
    prices = [p[1] for p in coin_data["market_data"]["sparkline_7d"]["price"]]
    if len(prices) < period:
        return prices[-1] if prices else 0.0
    ma = sum(prices[-period:]) / period
    return round(ma, 4)

async def fetch_all_coin_data():
    coin_ids = [coin["id"] for coin in TELEGRAM_WALLET_COINS]
    url = f"https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
        "sparkline": "true"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            markets_data = await response.json()

    coin_data = {}
    for item in markets_data:
        try:
            coin_id = item["id"]
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=true"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    full_data = await response.json()
                    coin_data[coin_id] = full_data
        except Exception:
            continue

    return coin_data
