import httpx
import logging

# Для tracking.py (отслеживание одной монеты)
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

# Для analysis.py (анализ всех монет списком)
async def get_current_price_batch(coin_ids, vs_currency="usd"):
    ids_param = ",".join(coin_ids)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies={vs_currency}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.warning(f"Ошибка при получении данных: {e}")
        return {}
