import logging
from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}
ANALYSIS_LOG = []

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def normalize_coin(raw_coin):
    """Гарантирует, что все ключи имеют float вместо None."""
    return {
        "id": raw_coin.get("id", ""),
        "symbol": raw_coin.get("symbol", "?"),
        "rsi": safe_float(raw_coin.get("rsi")),
        "ma7": safe_float(raw_coin.get("ma7")),
        "current_price": safe_float(raw_coin.get("current_price")),
        "price_change_percentage_24h": safe_float(raw_coin.get("price_change_percentage_24h")),
        "total_volume": safe_float(raw_coin.get("total_volume")),
    }

def evaluate_coin(coin):
    rsi = coin["rsi"]
    ma7 = coin["ma7"]
    price = coin["current_price"]
    change_24h = coin["price_change_percentage_24h"]
    volume = coin["total_volume"]
    symbol = coin["symbol"].upper()

    reasons = []
    score = 0

    if 45 <= rsi <= 65:
        score += 1
    else:
        reasons.append(f"RSI {rsi} вне диапазона 45–65")

    if price > ma7:
        score += 1
    else:
        reasons.append(f"Цена ${price} ниже MA7 ${ma7}")

    if change_24h >= 1.5:
        score += 1
    else:
        reasons.append(f"Изменение за 24ч {change_24h}% недостаточно")

    if volume >= 1_000_000:
        score += 1
    else:
        reasons.append(f"Объём {volume} меньше 1M")

    rsi_weight = 1 if 45 <= rsi <= 65 else 0
    ma_weight = 1 if price > ma7 else 0
    change_weight = min(change_24h / 5, 1)
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
        logger.info(f"Получено {len(all_data)} монет с CoinGecko")
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        return []

    candidates = []
    for raw_coin in all_data:
        if raw_coin.get("id") in EXCLUDE_IDS:
            continue

        coin = normalize_coin(raw_coin)
        score, prob = evaluate_coin(coin)
        if score >= 3:
            coin["score"] = score
            coin["probability"] = prob
            candidates.append(coin)

    logger.info(f"Отобрано {len(candidates)} монет из {len(all_data)}")

    candidates.sort(
        key=lambda x: (safe_float(x.get("probability")), safe_float(x.get("price_change_percentage_24h"))),
        reverse=True,
    )

    top_signals = [
        {
            "id": c["id"],
            "symbol": c["symbol"],
            "current_price": c["current_price"],
            "price_change_percentage_24h": round(c["price_change_percentage_24h"], 2),
            "probability": c["probability"],
        }
        for c in candidates[:6]
    ]

    if not top_signals:
        logger.warning("⚠️ Нет подходящих монет даже после упрощённого фильтра.")

    return top_signals
