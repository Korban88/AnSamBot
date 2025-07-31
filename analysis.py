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


def format_volume(volume):
    """Форматируем объём в удобный вид"""
    if volume >= 1_000_000_000:
        return f"{round(volume / 1_000_000_000, 2)}B"
    elif volume >= 1_000_000:
        return f"{round(volume / 1_000_000, 2)}M"
    elif volume >= 1_000:
        return f"{round(volume / 1_000, 2)}K"
    else:
        return str(volume)


def evaluate_coin(coin):
    rsi = safe_float(coin.get("rsi"))
    ma7 = safe_float(coin.get("ma7"))
    price = safe_float(coin.get("current_price"))
    change_24h = safe_float(coin.get("price_change_percentage_24h"))
    change_7d = safe_float(coin.get("price_change_percentage_7d", 0))
    volume = safe_float(coin.get("total_volume"))
    symbol = coin.get("symbol", "?").upper()

    reasons = []
    score = 0

    # RSI check
    if 52 <= rsi <= 58:
        score += 1
        reasons.append(f"✓ RSI {rsi} (в норме)")
    else:
        reasons.append(f"✗ RSI {rsi} (вне диапазона 52–58)")

    # MA7 check
    if ma7 > 0 and price > ma7:
        score += 1
        reasons.append(f"✓ Цена выше MA7 ({ma7})")
    else:
        reasons.append(f"✗ Цена ниже MA7 ({ma7})")

    # Change 24h check
    if change_24h >= 3.0:
        score += 1
        reasons.append(f"✓ Рост за 24ч {change_24h}%")
    else:
        reasons.append(f"✗ Рост за 24ч {change_24h}% (мало)")

    # Weekly trend check
    if change_7d != 0:
        if change_7d >= 0:
            score += 1
            reasons.append(f"✓ Тренд за 7д {change_7d}%")
        else:
            reasons.append(f"✗ Тренд за 7д {change_7d}% (просадка)")
    else:
        reasons.append("✗ Данные по 7д недоступны")

    # Volume check
    if volume >= 10_000_000:
        score += 1
        reasons.append(f"✓ Объём {format_volume(volume)}")
    else:
        reasons.append(f"✗ Объём {format_volume(volume)} (<10M)")

    # Probability calculation
    rsi_weight = 1 if 52 <= rsi <= 58 else 0
    ma_weight = 1 if ma7 > 0 and price > ma7 else 0
    change_weight = min(change_24h / 5, 1) if change_24h > 0 else 0
    volume_weight = 1 if volume >= 10_000_000 else 0
    trend_weight = 1 if change_7d > 0 else 0

    prob = 70 + (rsi_weight + ma_weight + change_weight + volume_weight + trend_weight) * 4.5
    prob = round(min(prob, 93), 2)

    if score >= 4:
        ANALYSIS_LOG.append(f"✅ {symbol}: score={score}, prob={prob}%")
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
            coin["reasons"] = reasons
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
            "reasons": coin["reasons"],
            "safe": True
        }
        top_signals.append(signal)

    # fallback
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
                "reasons": ["⚠️ Fallback: рискованный выбор (нет идеальных монет)"],
                "safe": False
            })
            ANALYSIS_LOG.append(f"⚠️ {best['symbol'].upper()}: выбран как fallback")

    if not top_signals:
        logger.warning("⚠️ Нет подходящих монет даже после фильтрации.")

    return top_signals
