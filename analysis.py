import random
import logging
from crypto_utils import get_all_prices

logger = logging.getLogger(__name__)

def calculate_probability(score: float) -> int:
    return min(95, max(30, int(score * 100)))

def build_signal(coin: str, price: float, score: float) -> dict:
    target_price = round(price * 1.05, 4)
    stop_loss = round(price * 0.96, 4)
    return {
        "coin": coin,
        "entry_price": price,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "probability": calculate_probability(score)
    }

async def get_top_signals() -> list:
    from crypto_list import crypto_list
    prices = await get_all_prices(crypto_list)
    signals = []

    for coin in crypto_list:
        price = prices.get(coin)
        if not price:
            logger.warning(f"Нет цены для {coin} в batch-ответе: {price}")
            continue

        score = random.uniform(0.6, 0.9)  # здесь позже будет реальный анализ
        signal = build_signal(coin, price, score)

        if signal["probability"] >= 65:
            signals.append(signal)

    signals.sort(key=lambda x: x["probability"], reverse=True)
    return signals[:3]
