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
    if price >= 1:
        return round(price, 3)
    elif price >= 0.01:
        return round(price, 4)
    else:
        return round(price, 6)


def format_volume(volume):
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
    change_7d = coin.get("price_change_percentage_7d")
    volume = safe_float(coin.get("total_volume"))
    symbol = coin.get("symbol", "?").upper()

    # Проверяем на отсутствие данных
    if price == 0 or rsi == 0 or volume == 0:
        ANALYSIS_LOG.append(f"⚠️ {symbol}: нет данных от CoinGecko")
        return None, None, None

    reasons = []
    score = 0

    # RSI check
    if 50 <= rsi <= 60:
        score += 1
        reasons.append(f"✓ RSI {rsi} (в норме)")
    else:
        reasons.append(f"✗ RSI {rsi} (вне диапазона 50–60)")

    # MA7 check
    if ma7 > 0 and price > ma7:
        score += 1
        reasons.append(f"✓ Цена выше MA7 ({ma7})")
    else:
        reasons.append(f"✗ Цена ниже MA7 ({ma7})")

    # Change 24h check
    if change_24h >= 2.5:
        score += 1
        reasons.append(f"✓ Рост за 24ч {change_24h}%")
    else:
        reasons.append(f"✗ Рост за 24ч {change_24h}% (мало)")

    # Weekly trend check (если данных нет — не штрафуем)
    if change_7d is not None:
        if change_7d > 0:
            score += 1
            reasons.append(f"✓ Тренд за 7д {change_7d}%")
        elif change_7d < 0:
            reasons.append(f"✗ Тренд за 7д {change_7d}% (просадка)")
        else:
            reasons.append("⚠️ Данные по 7д отсутствуют, не учитываем")
    else:
        reasons.append("⚠️ Данные по 7д отсутствуют (не штрафуем)")

    # Volume check
    if volume >= 5_000_000:
        score += 1
        reasons.append(f"✓ Объём {format_volume(volume)}")
    else:
        reasons.append(f"✗ Объём {format_volume(volume)} (<5M)")

    # Probability
    rsi_weight = 1 if 50 <= rsi <= 60 else 0
    ma_weight = 1 if ma7 > 0 and price > ma7 else 0
    change_weight = min(change_24h / 5, 1) if change_24h > 0 else 0
    volume_weight = 1 if volume >= 5_000_000 else 0
    trend_weight = 1 if change_7d and change_7d > 0 else 0

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
        logger.info(f"🔍 Всего монет для анализа: {len(coin_ids)}")
        all_data = await get_all_coin_data(coin_ids)
        logger.info(f"📊 Данные получены по {len(all_data)} монетам из {len(coin_ids)}")

        if len(all_data) < len(coin_ids):
            missing_ids = set(coin_ids) - {c.get("id") for c in all_data}
            ANALYSIS_LOG.append(f"⚠️ Нет данных по {len(missing_ids)} монетам: {', '.join(list(missing_ids)[:10])}...")
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        return []

    candidates = []
    no_data_count = 0
    for coin in all_data:
        coin_id = coin.get("id", "")
        symbol = coin.get("symbol", "?").upper()

        if coin_id in EXCLUDE_IDS:
            ANALYSIS_LOG.append(f"⛔ {symbol}: исключено вручную (в EXCLUDE_IDS)")
            continue

        try:
            score, prob, reasons = evaluate_coin(coin)
            if score is None:  # Монета без данных
                no_data_count += 1
                continue
        except Exception as e:
            ANALYSIS_LOG.append(f"⚠️ {symbol}: ошибка при анализе — {str(e)}")
            continue

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
        for fallback_coin in all_data:
            if fallback_coin.get("id") in EXCLUDE_IDS:
                continue
            symbol = fallback_coin.get("symbol", "?").upper()
            price = round_price(safe_float(fallback_coin.get("current_price")))
            change = round(safe_float(fallback_coin.get("price_change_percentage_24h")), 2)
            volume = safe_float(fallback_coin.get("total_volume", 0))

            if price and change and volume >= 5_000_000:
                top_signals.append({
                    "id": fallback_coin["id"],
                    "symbol": fallback_coin["symbol"],
                    "current_price": price,
                    "price_change_percentage_24h": change,
                    "probability": 65.0,
                    "reasons": ["⚠️ Fallback: рискованный выбор (нет идеальных монет)"],
                    "safe": False
                })
                ANALYSIS_LOG.append(f"⚠️ {symbol}: выбран как fallback")
                break

    passed = len(candidates)
    excluded = len([c for c in all_data if c.get("id") in EXCLUDE_IDS])
    ANALYSIS_LOG.append(f"📊 Статистика анализа: получено {len(all_data)} из {len(coin_ids)}, исключено {excluded}, без данных {no_data_count}, прошло фильтр {passed}")

    if not top_signals:
        logger.warning("⚠️ Нет подходящих монет даже после фильтрации.")

    return top_signals
