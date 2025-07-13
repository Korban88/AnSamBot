import httpx

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

COINS = ["bitcoin", "ethereum", "toncoin"]

async def fetch_prices():
    params = {
        "ids": ",".join(COINS),
        "vs_currencies": "usd"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(COINGECKO_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {coin: data.get(coin, {}).get("usd", "нет данных") for coin in COINS}
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return {}
