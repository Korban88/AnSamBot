import httpx

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

async def get_change_and_price_batch(coin_ids: list) -> dict:
    ids_param = ",".join(coin_ids)
    params = {
        "ids": ids_param,
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(COINGECKO_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            result = {
                coin_id: {
                    "change_24h": float(data.get(coin_id, {}).get("usd_24h_change", 0.0)),
                    "price": float(data.get(coin_id, {}).get("usd", 0.0))
                } for coin_id in coin_ids
            }
            return result
    except Exception as e:
        print(f"Ошибка при пакетном получении данных: {e}")
        return {coin_id: {"change_24h": 0.0, "price": 0.0} for coin_id in coin_ids}

async def get_rsi_mock(coin_id: str) -> float:
    return 55.0
