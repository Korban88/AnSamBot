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

def round_price(price):
    """Ограничиваем количество знаков после запятой"""
    if price >= 1:
        return round(price, 3)
    elif price >= 0.01:
        return round(price, 4)
    else:
        return round(price, 6)

def evaluate_coin(coin):
    rsi = safe_float(coin.get("rsi"))
    ma7 = safe_float(coin.get("ma7"))
    price = safe_float(coin.get("current_price"))
    change_24h = safe_float(coin.get("price_change_percentage_24h"))
    volume = safe_float(coin.get("total_volume"))
    change_7d = safe_float(coin.get("price_change_percentage_7d", 0))
    symbol = coin.get("symbol", "?").upper()

    reasons = []
    score = 0

    # RSI check
    if 50 <= rsi <= 60:
        score += 1
    else:
        reasons.append(f"RSI {rsi} вне диапазона 50–60")

    # MA7 check
    if ma7 > 0 and price > ma7:
        score += 1
    else:
        reasons.append(f"Цена ${price} ниже MA7 ${ma7}")

    # Change 24h check (≥2%)
    if change_24h >= 2.0:
        score += 1
    else:
        reasons.append(f"Изменение за 24ч {change_24h}% недостаточно (нужно ≥2%)")

    # Weekly trend check
    if change_7d > -5.0:
        score += 1
    else:
        reasons.append(f"Просадка за 7д {change_7d}% слишком велика")

    # Volume check
    if volume >= 5_000_000:
        score += 1
    else:
        reasons.append(f"Объём {volume} < 5M")

    # Probability calculation (реалистично)
    rsi_weight = 1 if 50 <= rsi <= 60 else 0
    ma_weight = 1 if ma7 > 0 and price > ma7 else 0
    change_weight = min(change_24h / 5, 1) if change_24h > 0 else 0
    volume_weight = 1 if volume >= 5_000_000 else 0
    trend_weight = 1 if change_7d > -5 else 0

    prob = 75 + (rsi_weight + ma_weight + change_weight + volume_weight + trend_weight) * 3.5
    prob = round(min(prob, 93), 2)

    if score >= 4:
        ANALYSIS_LOG.append(f"✅ {symbol}: score={score}, prob={prob}%")
    else:
        ANALYSIS_LOG.append(f"❌ {symbol}: отклонено — {', '.join(reasons)}")

    return score, prob

async def analyze_cryptos(fallback=True):
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
        if score >= 4:
            coin["score"] = score
            coin["probability"] = prob
            coin["current_price"] = round_price(safe_float(coin.get("current_price")))
            coin["price_change_percentage_24h"] = round(safe_float(coin.get("price_change_percentage_24h")), 2)
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
            "current_price": coin["current_price"],
            "price_change_percentage_24h": coin["price_change_percentage_24h"],
            "probability": coin["probability"],
            "safe": True
        }
        top_signals.append(signal)

    # fallback (если нет идеальных)
    if not top_signals and fallback:
        all_data.sort(key=lambda x: safe_float(x.get("price_change_percentage_24h")), reverse=True)
        best = all_data[0] if all_data else None
        if best:
            top_signals.append({
                "id": best["id"],
                "symbol": best["symbol"],
                "current_price": round_price(safe_float(best.get("current_price"))),
                "price_change_percentage_24h": round(safe_float(best.get("price_change_percentage_24h")), 2),
                "probability": 65.0,
                "safe": False
            })
            ANALYSIS_LOG.append(f"⚠️ {best['symbol'].upper()}: выбран как fallback (рискованный сигнал)")

    if not top_signals:
        logger.warning("⚠️ Нет подходящих монет даже после фильтрации.")

    return top_signals
