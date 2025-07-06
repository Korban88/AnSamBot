import aiohttp
import asyncio

# Получение текущей цены монеты
async def get_current_price(coin_id: str):
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                return data[coin_id]["usd"]
    except Exception:
        return None

# Получение скользящей средней
async def get_moving_average(coin_id: str, days: int = 14):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                prices = [price[1] for price in data["prices"]]
                if len(prices) < days:
                    return None
                ma = sum(prices[-days:]) / days
                return ma
    except Exception:
        return None

# Получение RSI
async def get_rsi(coin_id: str, period: int = 14):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": period + 1}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                closes = [price[1] for price in data["prices"]]
                if len(closes) < period + 1:
                    return None

                gains = []
                losses = []
                for i in range(1, len(closes)):
                    delta = closes[i] - closes[i - 1]
                    if delta > 0:
                        gains.append(delta)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(delta))

                average_gain = sum(gains[-period:]) / period
                average_loss = sum(losses[-period:]) / period
                if average_loss == 0:
                    return 100
                rs = average_gain / average_loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
    except Exception:
        return None

# Получение цен всех монет из списка
async def fetch_all_coin_data(coin_ids: list):
    try:
        ids_param = ",".join(coin_ids)
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": ids_param, "vs_currencies": "usd"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return {}
                return await response.json()
    except Exception:
        return {}
