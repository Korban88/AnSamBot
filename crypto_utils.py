import aiohttp

SYMBOL_ID_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "TON": "toncoin",
    "BNB": "binancecoin",
    "TRX": "tron",
    "DOGE": "dogecoin",
    "SHIB": "shiba-inu",
    "XRP": "ripple"
}

async def get_market_data():
    url = f"https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(SYMBOL_ID_MAP.values()),
        "price_change_percentage": "24h",
        "sparkline": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                raw_data = await resp.json()
                result = []
                for item in raw_data:
                    symbol = next((k for k, v in SYMBOL_ID_MAP.items() if v == item["id"]), None)
                    if not symbol:
                        continue

                    result.append({
                        "symbol": symbol,
                        "current_price": item["current_price"],
                        "price_change_percentage_24h": item["price_change_percentage_24h_in_currency"],
                        "rsi": 50 + (item["price_change_percentage_24h_in_currency"] or 0) / 2,
                        "ma": item["current_price"] * 0.98
                    })
                return result
            return []

async def get_price(symbol):
    coin_id = SYMBOL_ID_MAP.get(symbol.upper())
    if not coin_id:
        return None

    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin_id, "vs_currencies": "usd"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get(coin_id, {}).get("usd")
            return None
