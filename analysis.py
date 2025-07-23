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

    if change_24h < -5 and not fallback:
        log = f"❌ {symbol}: сильное падение за 24ч {change_24h:.2f}% — исключено"
        ANALYSIS_LOG.append(log)
        logger.info(log)
        return -100, 0

    if change_24h < -7 and fallback:
        log = f"❌ {symbol}: падение {change_24h:.2f}% даже в fallback — исключено"
        ANALYSIS_LOG.append(log)
        logger.info(log)
        return -100, 0

    score = 0
    log_parts = []

    # RSI
    if not fallback:
        if 50 <= rsi <= 60:
            score += 2
            log_parts.append(f"✅ RSI={rsi}")
        elif 45 <= rsi < 50 or 60 < rsi <= 65:
            score += 1
            log_parts.append(f"⚠️ RSI на грани: {rsi}")
        else:
            log_parts.append(f"🔸 RSI вне зоны ({rsi})")
    else:
        if 45 <= rsi <= 65:
            score += 1
            log_parts.append(f"⚠️ RSI в широком диапазоне: {rsi}")
        else:
            log_parts.append(f"🔸 RSI вне даже fallback диапазона ({rsi})")

    # MA7
    if price > ma7:
        score += 2
        log_parts.append(f"✅ Цена выше MA7 (P={price} > MA7={ma7})")
    else:
        if fallback:
            log_parts.append(f"🔸 Цена ниже MA7 (fallback режим)")
        else:
            log_parts.append(f"🔸 Цена ниже MA7 (P={price} < MA7={ma7})")

    # 24ч изменение
    if change_24h > 5:
        score += 2
        log_parts.append(f"✅ Рост 24ч: {change_24h:.2f}%")
    elif change_24h > 2:
        score += 1
        log_parts.append(f"⚠️ Умеренный рост 24ч: {change_24h:.2f}%")
    elif 0 > change_24h >= -5:
        if (rsi < 45 or price < ma7) and not fallback:
            log = f"❌ {symbol}: падение {change_24h:.2f}% и нет признаков разворота"
            ANALYSIS_LOG.append(log)
            logger.info(log)
            return -100, 0
        else:
            log_parts.append(f"⚠️ Падение {change_24h:.2f}%, но возможен разворот")
    elif fallback and -7 < change_24h < 0:
        log_parts.append(f"🔸 Небольшое падение в fallback: {change_24h:.2f}%")

    # Вероятность
    base_prob = 45 if not fallback else 40
    multiplier = 7 if not fallback else 6
    probability = min(90, base_prob + score * multiplier)
    probability = round(probability, 2)

    ANALYSIS_LOG.append(f"🔍 {symbol}: " + "; ".join(log_parts) + f" → score={score}, prob={probability}%")
    return score, probability

async def analyze_cryptos(fallback=False):
    global ANALYSIS_LOG
    ANALYSIS_LOG = []  # сброс логов

    coin_ids = TELEGRAM_WALLET_COIN_IDS if isinstance(TELEGRAM_WALLET_COIN_IDS, list) else list(TELEGRAM_WALLET_COIN_IDS.keys())
    all_data = await get_all_coin_data(coin_ids)

    candidates = []

    for coin in all_data:
        coin_id = coin.get("id")
        if not coin_id or coin_id in EXCLUDE_IDS:
            continue

        score, probability = evaluate_coin(coin, fallback=fallback)

        if not fallback:
            if score < 2 or probability < 65:
                log = f"⛔ {coin['symbol'].upper()}: score={score}, prob={probability}% — отклонена"
                ANALYSIS_LOG.append(log)
                continue
        else:
            if score < 1 or probability < 55:
                log = f"⛔ {coin['symbol'].upper()} (fallback): score={score}, prob={probability}% — отклонена"
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
