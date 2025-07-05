import httpx

API_URL = "https://api.coingecko.com/api/v3/simple/price"

async def get_current_price(coin_id: str) -> float | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(API_URL, params={"ids": coin_id, "vs_currencies": "usd"})
            data = response.json()
            return data.get(coin_id, {}).get("usd")
    except Exception as e:
        return None

async def get_all_prices(coin_ids: list[str]) -> dict[str, float]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(API_URL, params={"ids": ",".join(coin_ids), "vs_currencies": "usd"})
            return {coin: response.json().get(coin, {}).get("usd") for coin in coin_ids}
    except Exception:
        return {}
