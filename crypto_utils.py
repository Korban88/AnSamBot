import httpx

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
RSI_API_URL = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"

async def get_change_24h_batch(coin_ids: list) -> dict:
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
            changes = {coin_id: float(data.get(coin_id, {}).get("usd_24h_change", 0.0)) for coin_id in coin_ids}
            return changes
    except Exception as e:
        print(f"Ошибка при пакетном получении 24h change: {e}")
        return {coin_id: 0.0 for coin_id in coin_ids}

async def get_rsi_mock(coin_id: str) -> float:
    return 55.0
