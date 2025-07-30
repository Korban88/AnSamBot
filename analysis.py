import logging
from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}
ANALYSIS_LOG = []

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def evaluate_coin(coin):
    rsi = safe_float(coin.get("rsi"))
    ma7 = safe_float(coin.get("ma7"))
    ma30 = safe_float(coin.get("ma30"))  # добавим поддержку MA30
    price = safe_float(coin.get("current_price"))
    change_24h = safe_float(coin.get("price_change_percentage_24h"))
    change_7d = safe_float(coin.get("price_change_percentage_7d_in_currency"))
    volume = safe_float(coin.get("total_volume"))
    symbol = coin.get("symbol", "?").upper()

    reasons = []
    score = 0

    # RSI check
    if rsi > 0 and 45 <= rsi <= 65:
        score += 1
    else:
        reasons.append(f"RSI {rsi} вне диапазона 45–65 или отсутствует")

    # MA7 и MA30 check
    if ma7 > 0 and price > ma7:
        if ma30 > 0:
            if ma7 >= ma30:
                score += 1
            else:
                reasons.append(f"MA7 {ma7} ниже MA30 {ma30}")
        else:
            score += 1
    else:
        reasons.append(f"Цена ${price} ниже или нет MA7 ${ma7}")

    # Изменение за 24ч
    if change_24h >= 1.5:
        score += 1
    else:
        reasons.append(f"Изменение за 24ч {change_24h}% недостаточно")

    # Объём
    if volume >= 1_000_000:
        score += 1
    else:
        reasons.append(f"Объём {volume} меньше 1M или отсутствует")

    # Просадка за 7 дней
    if change_7d <= -7:
        reasons.append(f"Просадка за 7д {change_7d}%")
        score = 0  # аннулируем монету сразу

    # Жёсткий стоп: падение за сутки ≥ -3%
    if change_24h <= -3:
        reasons.append(f"Суточное падение {change_24h}%")
        score = 0

    # Probability calculation
    rsi_weight = 1 if rsi > 0 and 45 <= rsi <= 65 else 0
    ma_weight = 1 if ma7 > 0 and price > ma7 and (ma30 == 0 or ma7 >= ma30) else 0
    change_weight = min(change_24h / 5, 1) if change_24h > 0 else 0
    volume_weight = 1 if volume >= 1_000_000 else 0

    prob = 50 + (rsi_weight + ma_weight + change_weight + volume_weight) * 11.25
    prob = round(min(prob, 95), 2)

    if score >= 3:
        ANALYSIS_LOG.append(f"✅ {symbol}: score={score}, prob={prob}%")
    else:
        ANALYSIS_LOG.append(f"❌ {symbol}: отклонено — {', '.join(reasons)}")

    return score, prob


async def analyze_cryptos(fallback=False):
    global ANALYSIS_LOG
    ANALYSIS_LOG.clear()

    try:
        coin_ids = list(TELEGRAM_WALLET_COIN_IDS.keys())
        all_data = await get_all_coin_data(coin_ids)
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        return []

    candidates = []

    for coin in all_data:
        if coin.get("id") in EXCLUDE_IDS:
            continue

        score, prob = evaluate_coin(coin)
        if score >= 3:
            coin["score"] = score
            coin["probability"] = prob
            coin["price_change_percentage_24h"] = safe_float(coin.get("price_change_percentage_24h"))
            candidates.append(coin)

    candidates.sort(key=lambda x: (
        safe_float(x.get("probability")),
        safe_float(x.get("price_change_percentage_24h"))
    ), reverse=True)

    top_signals = []
    for coin in candidates[:6]:
        signal = {
            "id": coin["id"],
            "symbol": coin["symbol"],
            "current_price": safe_float(coin.get("current_price")),
            "price_change_percentage_24h": round(safe_float(coin.get("price_change_percentage_24h")), 2),
            "probability": coin["probability"]
        }
        top_signals.append(signal)

    if not top_signals:
        logger.warning("⚠️ Нет подходящих монет даже после усиленного анализа.")

    return top_signals
