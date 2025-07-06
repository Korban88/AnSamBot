import aiohttp
import asyncio
import time
from crypto_list import TELEGRAM_WALLET_COINS

API_BASE = "https://api.binance.com/api/v3"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


async def fetch_coin_data(session, symbol):
    url = f"{API_BASE}/ticker/24hr?symbol={symbol}USDT"
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "symbol": symbol,
                    "price": float(data["lastPrice"]),
                    "price_change_percent": float(data["priceChangePercent"]),
                    "volume": float(data["quoteVolume"])
                }
    except Exception:
        return None


async def fetch_all_coin_data():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_coin_data(session, coin) for coin in TELEGRAM_WALLET_COINS]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]


async def get_current_price(symbol):
    url = f"{API_BASE}/ticker/price?symbol={symbol}USDT"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=10) as response:
                data = await response.json()
                return float(data["price"])
    except Exception:
        return None
