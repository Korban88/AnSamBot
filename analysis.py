import logging
from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}  # стабильные монеты
ANALYSIS_LOG = []  # лог анализа для /debug_analysis

def evaluate_coin(coin, fallback=False):
    rsi = coin.get("rsi", 0)
    ma7 = coin.get("ma7", 0)
    price = coin.get("current_price", 0)
    change_24h = coin.get("price_change_percentage_24h", 0)
    symbol = coin.get("symbol", "?").upper()

    if not rsi or not ma7 or not price:
        log = f"❌ {symbol}: недостаточно данных (RSI={rsi}, MA7={ma7}, Price={price})"
        ANALYSIS_LOG.append(log)
        logger.info(log)
        return -100, 0

    if change_24h < -7:
        log = f"❌ {symbol}: падение {change_24h:.2f}% — исключено"
        ANALYSIS_LOG.append(log)
        logger.info(log)
        return -100, 0

    score = 0
    log_parts = []

    # RSI
    if 50 <= rsi <= 60:
        score += 2
        log_parts.append(f"✅ RSI={rsi}")
    elif 45 <= rsi < 50 or 60 < rsi <= 70:
        score += 1
        log_parts.append(f"⚠️ RSI допустимый: {rsi}")
    else:
        log_parts.append(f"🔸 RSI вне зоны: {rsi}")

    # MA7
    if price > ma7:
        score += 2
        log_parts.append(f"✅ Цена выше MA7 (P={price} > MA7={ma7})")
    elif price >= ma7 * 0.98:
        score += 1
        log_parts.append(f"⚠️ Цена немного ниже MA7 (P={price} < MA7={ma7})")
    else:
        log_parts.append(f"🔸 Цена ниже MA7 (P={price} < MA7={ma7})")

    # 24h изменение
    if change_24h > 5:
        score += 2
        log_parts.append(f"✅ Рост 24ч: {change_24h:.2f}%")
    elif change_24h > 2:
        score += 1
        log_parts.append(f"⚠️ Умеренный рост 24ч: {change_24h:.2f}%")
    elif 0 > change_24h >= -5:
        if rsi >= 50 and price >= ma7:
            score += 1
            log_parts.append(f"⚠️ Падение, но признаки разворота: {change_24h:.2f}%")
        else:
            log = f"❌ {symbol}: падение {change_24h:.2f}% без признаков разворота"
            ANALYSIS_LOG.append(log)
            logger.info(log)
            return -100, 0
    else:
        log_parts.append(f"🔸 Незначительное падение: {change_24h:.2f}%")

    # Расчёт вероятности
    base_prob = 45
    multiplier = 7
    probability = min(90, base_prob + score * multiplier)
    probability = round(probability, 2)

    log_line = f"🔍 {symbol}: " + "; ".join(log_parts) + f" → score={score}, prob={probability}%"
    ANALYSIS_LOG.append(log_line)
    logger.info(log_line)

    return score, probability

async def analyze_cryptos(fallback=False):
    global ANALYSIS_LOG
    ANALYSIS_LOG.clear()

    coin_ids = TELEGRAM_WALLET_COIN_IDS if isinstance(TELEGRAM_WALLET_COIN_IDS, list) else list(TELEGRAM_WALLET_COIN_IDS.keys())
    all_data = await get_all_coin_data(coin_ids)

    candidates = []

    for coin in all_data:
        coin_id = coin.get("id")
        if not coin_id or coin_id in EXCLUDE_IDS:
            continue

        score, probability = evaluate_coin(coin, fallback=fallback)

        if score < 2 or probability < 60:
            log = f"⛔ {coin['symbol'].upper()}: score={score}, prob={probability}% — отклонена"
            ANALYSIS_LOG.append(log)
            continue

        coin["score"] = score
        coin["probability"] = probability
        candidates.append(coin)
        ANALYSIS_LOG.append(f"✅ {coin['symbol'].upper()}: ДОБАВЛЕНА в топ (score={score}, prob={probability}%)")

    candidates.sort(key=lambda x: x["probability"], reverse=True)

    top_signals = []
    for coin in candidates[:6]:
        signal = {
            "id": coin["id"],
            "symbol": coin["symbol"],
            "current_price": coin["current_price"],
            "price_change_percentage_24h": round(coin.get("price_change_percentage_24h", 0), 2),
            "probability": coin["probability"]
        }
        top_signals.append(signal)

    if not top_signals:
        logger.info("⚠️ Нет подходящих монет по фильтрам.")

    return top_signals
