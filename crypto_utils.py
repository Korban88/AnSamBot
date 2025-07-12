import httpx
import logging

async def fetch_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,toncoin",
        "vs_currencies": "usd"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {coin: data[coin]["usd"] for coin in data}
    except Exception as e:
        logging.error(f"Ошибка при получении цен: {e}")
        return {}
