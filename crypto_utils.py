import httpx

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
RSI_API_URL = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"

async def get_change_24h(coin_id: str) -> float:
    params = {
        "ids": coin_id,
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(COINGECKO_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            change = data.get(coin_id, {}).get("usd_24h_change", 0.0)
            return float(change)
    except Exception as e:
        print(f"Ошибка при получении 24h change для {coin_id}: {e}")
        return 0.0

async def get_rsi_mock(coin_id: str) -> float:
    return 55.0
