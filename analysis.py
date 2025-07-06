import logging
from crypto_utils import get_current_price, get_moving_average, get_rsi

logger = logging.getLogger("analysis")

async def analyze_coin(coin):
    coin_id = coin["id"]
    try:
        current_price = coin.get("current_price")
        if current_price is None:
            current_price = await get_current_price(coin_id)
        if current_price is None:
            logger.warning(f"⚠️ Пропуск {coin_id}: нет текущей цены")
            return None

        ma = await get_moving_average(coin_id)
        rsi = await get_rsi(coin_id)

        if ma is None and rsi is None:
            logger.warning(f"⚠️ Нет MA и RSI для {coin_id}, пропускаем")
            return None

        ma_score = 0
        if ma:
            ma_score = max(0, min(1, (current_price - ma) / ma))

        rsi_score = 0
        if rsi:
            if 50 < rsi < 70:
                rsi_score = (rsi - 50) / 20
            elif rsi >= 70:
                rsi_score = 0.1  # перекупленность

        change_24h = coin.get("price_change_percentage_24h", 0)
        if change_24h is None:
            change_24h = 0

        if change_24h < -3:
            logger.info(f"❌ {coin_id} отфильтрован: падение за 24ч {change_24h:.2f}%")
            return None

        growth_score = max(0, min(1, change_24h / 5))  # рост до 5% — максимум

        score = 0.5 * ma_score + 0.3 * rsi_score + 0.2 * growth_score
        probability = round(50 + score * 50)

        if probability < 65:
            return None

        return {
            "id": coin_id,
            "symbol": coin.get("symbol"),
            "name": coin.get("name"),
            "current_price": current_price,
            "ma": ma,
            "rsi": rsi,
            "change_24h": change_24h,
            "probability": probability
        }

    except Exception as e:
        logger.error(f"⚠️ Ошибка при анализе {coin_id}: {e}")
        return None

async def analyze_cryptos(coin_data):
    results = []
    for coin in coin_data:
        result = await analyze_coin(coin)
        if result:
            results.append(result)

    logger.info(f"🎯 Монет после фильтрации: {len(results)}")

    sorted_results = sorted(results, key=lambda x: x["probability"], reverse=True)
    top_3 = sorted_results[:3]

    logger.info(f"🏆 Отобрано top-3 монет: {[coin['id'] for coin in top_3]}")
    return top_3
