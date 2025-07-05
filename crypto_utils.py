import httpx
import logging
import asyncio

# Для tracking.py — отслеживание одной монеты
async def get_current_price(coin_id, vs_currency="usd"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={vs_currency}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get(coin_id, {}).get(vs_currency)
    except Exception as e:
        logging.warning(f"Ошибка при получении цены для {coin_id}: {e}")
        return None

# Для analysis.py — анализ всех монет списком, с ограничением на лимиты API
async def get_current_price_batch(coin_ids, vs_currency="usd"):
    prices = {}
    batch_size = 20
    url = "https://api.coingecko.com/api/v3/simple/price"

    for i in range(0, len(coin_ids), batch_size):
        batch = coin_ids[i:i + batch_size]
        ids_param = ",".join(batch)
        params = {"ids": ids_param, "vs_currencies": vs_currency}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                prices.update(data)
        except Exception as e:
            logging.warning(f"Ошибка при получении batch {batch}: {e}")

        await asyncio.sleep(1)  # Пауза между батчами, чтобы избежать 429

    return prices
