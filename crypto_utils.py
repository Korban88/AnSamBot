import aiohttp
import asyncio
from crypto_list import CRYPTO_LIST

API_URL = "https://api.coingecko.com/api/v3/simple/price"

async def get_current_prices(ids):
    params = {
        "ids": ",".join(ids),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                print(f"Ошибка запроса данных: {resp.status}")
                return {}
