import aiohttp
import asyncio

API_URL = "https://api.coingecko.com/api/v3/simple/price"

async def get_current_prices(coin_ids):
    """
    Получает текущие цены и изменение за 24 часа для списка монет с CoinGecko.
    Возвращает словарь: {coin_id: {"usd": цена, "usd_24h_change": изменение}}
    """
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {}

def reset_top_signals_cache():
    """
    Заглушка-функция для совместимости с handlers.py.
    Реализация очистки кеша должна быть в analysis.py.
    """
    import os
    if os.path.exists("top_signals_cache.json"):
        os.remove("top_signals_cache.json")
