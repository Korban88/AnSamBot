import httpx
import asyncio
import logging
from crypto_list import crypto_list
from crypto_utils import get_current_price

logger = logging.getLogger("analysis")

def split_into_batches(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]

async def analyze_cryptos():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    headers = {"accept": "application/json"}
    params_base = {
        "vs_currency": "usd",
        "price_change_percentage": "24h",
    }

    cryptos_data = []

    for batch in split_into_batches(crypto_list, 20):
        params = params_base.copy()
        params["ids"] = ",".join(batch)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                cryptos_data.extend(data)
        except Exception as e:
            logger.warning(f"Ошибка при получении батча данных: {e}")
        await asyncio.sleep(1.2)  # 🛑 Пауза между батчами

    # Фильтрация
    filtered = []
    for coin in cryptos_data:
        price = coin["current_price"]
        change_24h = coin["price_change_percentage_24h"] or 0
        volume = coin["total_volume"] or 0

        if change_24h < -3:
            continue
        if volume < 1_000_000:
            continue

        score = (change_24h * 1.5) + (volume / 10_000_000)
        growth_probability = round(min(95, max(60, score)), 2)

        target_price = round(price * 1.05, 6)
        stop_loss = round(price * 0.97, 6)

        filtered.append({
            "name": coin["id"],
            "price": price,
            "growth_probability": growth_probability,
            "target_price": target_price,
            "stop_loss": stop_loss,
        })

    top3 = sorted(filtered, key=lambda x: x["growth_probability"], reverse=True)[:3]
    return top3
