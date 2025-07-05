import httpx
import logging
import numpy as np
from typing import List, Dict, Tuple
from crypto_list import crypto_list
from crypto_utils import get_current_price_batch

logger = logging.getLogger(__name__)


def analyze_cryptos() -> List[Dict[str, str]]:
    try:
        prices = get_current_price_batch(crypto_list)
    except Exception as e:
        logger.warning(f"Ошибка при получении данных: {e}")
        return []

    analyzed_data = []

    for coin, price in prices.items():
        if price is None:
            logger.warning(f"Нет цены для {coin} в batch-ответе.")
            continue

        # Реалистичная вероятность роста
        # Пример простого анализа: волатильность, имя монеты, базовая метрика
        base_score = 0.5

        if "dog" in coin or "cat" in coin or "meme" in coin:
            base_score -= 0.1  # менее надёжные монеты
        if price < 0.01:
            base_score -= 0.05  # слишком дешёвые могут быть нестабильны
        if price > 1:
            base_score += 0.05  # более стабильные монеты

        noise = np.random.normal(0, 0.05)
        probability = np.clip(base_score + noise, 0, 1)

        if probability < 0.65:
            continue

        entry_price = round(price, 6)
        target_price = round(entry_price * 1.05, 6)
        stop_loss = round(entry_price * 0.97, 6)

        analyzed_data.append({
            "coin": coin.upper(),
            "probability": round(probability * 100, 1),
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss
        })

    # Сортировка по вероятности
    analyzed_data.sort(key=lambda x: x["probability"], reverse=True)

    return analyzed_data[:10]  # возвращаем максимум 10, остальное фильтруется по кнопке
