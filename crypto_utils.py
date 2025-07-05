import asyncio
import httpx
import logging

async def get_current_price_batch(coin_ids, vs_currency="usd"):
    prices = {}
    chunk_size = 15
    for i in range(0, len(coin_ids), chunk_size):
        chunk = coin_ids[i:i+chunk_size]
        ids = ",".join(chunk)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies={vs_currency}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                chunk_prices = response.json()
                prices.update(chunk_prices)
        except httpx.HTTPStatusError as e:
            logging.warning(f"Ошибка при получении данных: {e}")
        await asyncio.sleep(1.5)  # задержка между запросами
    return prices
