import logging
from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}
ANALYSIS_LOG = []


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_coin(raw_coin):
    if not raw_coin or "id" not in raw_coin:
        return None
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

    prob = 50 + (min(score, 4)) * 11.25
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
        raw_data = await get_all_coin_data(coin_ids)

        all_data = []
        for c in raw_data:
            norm = normalize_coin(c)
            if norm:
                all_data.append(norm)
            else:
                logger.warning(f"⚠️ Пропущена монета: данные отсутствуют или некорректны {c}")
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        return []

    candidates = []
    for coin in all_data:
        if coin["id"] in EXCLUDE_IDS:
            continue

        score, prob = evaluate_coin(coin)
        if score >= 3:
            coin["score"] = score
            coin["probability"] = prob
            candidates.append(coin)

    candidates.sort(key=lambda x: (x["probability"], x["price_change_percentage_24h"]), reverse=True)

    top_signals = [{
        "id": c["id"],
        "symbol": c["symbol"],
        "current_price": c["current_price"],
        "price_change_percentage_24h": round(c["price_change_percentage_24h"], 2),
        "probability": c["probability"]
    } for c in candidates[:6]]

    if not top_signals and fallback and all_data:
        best = max(all_data, key=lambda x: x.get("price_change_percentage_24h", 0))
        top_signals = [{
            "id": best["id"],
            "symbol": best["symbol"],
            "current_price": best["current_price"],
            "price_change_percentage_24h": round(best["price_change_percentage_24h"], 2),
            "probability": 55.0
        }]
        ANALYSIS_LOG.append(f"⚠️ {best['symbol'].upper()} выбран в fallback-режиме")

    if not top_signals:
        logger.warning("⚠️ Нет подходящих монет даже после fallback.")

    return top_signals
