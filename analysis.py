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
    if 52 <= rsi <= 58:
        score += 1
        reasons.append(f"RSI: {rsi} (в норме)")
    else:
        reasons.append(f"RSI: {rsi} (вне диапазона 52–58)")

    # MA7 check
    if ma7 > 0 and price > ma7:
        score += 1
        reasons.append(f"MA7: {ma7} (цена выше)")
    else:
        reasons.append(f"MA7: {ma7} (цена ниже)")

    # Change 24h check
    if change_24h >= 3.0:
        score += 1
        reasons.append(f"Изменение 24ч: {change_24h}% (OK)")
    else:
        reasons.append(f"Изменение 24ч: {change_24h}% (мало)")

    # Weekly trend check
    if change_7d >= 0.0:
        score += 1
        reasons.append(f"Изменение 7д: {change_7d}% (OK)")
    else:
        reasons.append(f"Изменение 7д: {change_7d}% (просадка)")

    # Volume check
    if volume >= 10_000_000:
        score += 1
        reasons.append(f"Объём: ${volume} (OK)")
    else:
        reasons.append(f"Объём: ${volume} (<10M)")

    # Probability calculation (усиленный фильтр)
    rsi_weight = 1 if 52 <= rsi <= 58 else 0
    ma_weight = 1 if ma7 > 0 and price > ma7 else 0
    change_weight = min(change_24h / 6, 1) if change_24h > 0 else 0
    volume_weight = 1 if volume >= 10_000_000 else 0
    trend_weight = 1 if change_7d >= 0 else 0

    prob = 60 + (rsi_weight + ma_weight + change_weight + volume_weight + trend_weight) * 7
    prob = round(min(prob, 93), 2)

    # Логирование результата
    if score >= 4:
        ANALYSIS_LOG.append(f"✅ {symbol}: score={score}, prob={prob}%, причины: {', '.join(reasons)}")
    else:
        ANALYSIS_LOG.append(f"❌ {symbol}: отклонено — {', '.join(reasons)}")

    return score, prob, reasons


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

        score, prob, reasons = evaluate_coin(coin)
        if score >= 4:
            coin["score"] = score
            coin["probability"] = prob
            coin["current_price"] = round_price(safe_float(coin.get("current_price")))
            coin["price_change_percentage_24h"] = round(safe_float(coin.get("price_change_percentage_24h")), 2)
            coin["reasons"] = reasons
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
            "safe": True,
            "reasons": coin["reasons"]
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
                "safe": False,
                "reasons": ["Fallback: выбран по наибольшему росту 24ч"]
            })
            ANALYSIS_LOG.append(f"⚠️ {best['symbol'].upper()}: выбран как fallback (рискованный сигнал)")

    if not top_signals:
        logger.warning("⚠️ Нет подходящих монет даже после фильтрации.")

    return top_signals
