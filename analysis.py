import httpx
import logging
import numpy as np
from typing import List, Dict
from crypto_list import crypto_list
from crypto_utils import get_current_price_batch

logger = logging.getLogger(__name__)

async def analyze_cryptos() -> List[Dict[str, str]]:
    try:
        coin_ids = [coin["id"] for coin in crypto_list]
        prices_raw = await get_current_price_batch(coin_ids)
        prices = {k: v["usd"] for k, v in prices_raw.items() if "usd" in v}
    except Exception as e:
        logger.warning(f"Ошибка при получении данных: {e}")
        return []

    analyzed_data = []

    for coin, price in prices.items():
        if price is None:
            logger.warning(f"Нет цены для {coin} в batch-ответе.")
            continue

        base_score = 0.5

        if "dog" in coin or "cat" in coin or "meme" in coin:
            base_score -= 0.1
        if price < 0.01:
            base_score -= 0.05
        if price > 1:
            base_score += 0.05

        noise = np.random.normal(0, 0.05)
        probability = np.clip(base_score + noise, 0, 1)

        if probability < 0.65:
            continue

        entry_price = round(price, 6)
        target_price = round(entry_price * 1.05, 6)
        stop_loss = round(entry_price * 0.97, 6)

        analyzed_data.append({
            "name": coin.upper(),
            "growth_probability": round(probability * 100, 1),
            "price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss
        })

    analyzed_data.sort(key=lambda x: x["growth_probability"], reverse=True)
    return analyzed_data[:10]
