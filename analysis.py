import logging
from config import MIN_GROWTH_PROBABILITY
from crypto_utils import load_indicators

logger = logging.getLogger(__name__)

def analyze_cryptos():
    indicators = load_indicators()

    best_coin = None
    max_probability = 0

    for coin_id, data in indicators.items():
        if not data:
            logger.info(f"🔴 {coin_id} — нет данных")
            continue
        price = data.get("price")
        change_24h = data.get("change_24h")
        rsi = data.get("rsi")
        ma = data.get("ma")
        if price is None or change_24h is None:
            logger.info(f"🔴 {coin_id} — нет цены или изменения 24ч")
            continue
        # Упрощённая логика
        probability = 50 + (change_24h or 0) / 2
        if probability >= MIN_GROWTH_PROBABILITY and probability > max_probability:
            max_probability = probability
            best_coin = {
                "id": coin_id,
                "price": price,
                "change_24h": round(change_24h, 2),
                "rsi": rsi,
                "ma": ma,
                "target_percent": 5.0,
            }

    return best_coin
