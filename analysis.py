import logging
from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}  # стабильные монеты
ANALYSIS_LOG = []  # лог анализа для /debug_analysis

def evaluate_coin(coin):
    rsi = coin.get("rsi", 0)
    ma7 = coin.get("ma7", 0)
    price = coin.get("current_price", 0)
    change_24h = coin.get("price_change_percentage_24h", 0)
    symbol = coin.get("symbol", "?")

    if not rsi or not ma7 or not price:
        log = f"❌ {symbol.upper()}: недостаточно данных (rsi/ma7/price)"
        ANALYSIS_LOG.append(log)
        logger.info(log)
        return -100, 0

    if change_24h < -5:
        log = f"❌ {symbol.upper()}: падение за 24ч {change_24h:.2f}%"
        ANALYSIS_LOG.append(log)
        logger.info(log)
        return -100, 0

    score = 0

    if 50 <= rsi <= 60:
        score += 2
    elif 45 <= rsi < 50 or 60 < rsi <= 65:
        score += 1
    else:
        ANALYSIS_LOG.append(f"🔸 {symbol.upper()}: RSI вне зоны ({rsi})")

    if price > ma7:
        score += 2
    else:
        ANALYSIS_LOG.append(f"🔸 {symbol.upper()}: цена ниже MA7 (price={price}, ma7={ma7})")

    if change_24h > 5:
        score += 2
    elif change_24h > 2:
        score += 1
    elif 0 > change_24h >= -5:
        if (rsi < 45 or price < ma7):
            log = f"❌ {symbol.upper()}: падение {change_24h:.2f}% без признаков разворота"
            ANALYSIS_LOG.append(log)
            logger.info(log)
            return -100, 0
        else:
            ANALYSIS_LOG.append(f"✅ {symbol.upper()}: падение {change_24h:.2f}%, но есть признаки разворота")

    probability = max(0, min(90, 60 + score * 5))
    return score, round(probability, 2)

async def analyze_cryptos():
    global ANALYSIS_LOG
    ANALYSIS_LOG = []  # сброс логов

    coin_ids = TELEGRAM_WALLET_COIN_IDS if isinstance(TELEGRAM_WALLET_COIN_IDS, list) else list(TELEGRAM_WALLET_COIN_IDS.keys())
    all_data = await get_all_coin_data(coin_ids)

    candidates = []

    for coin in all_data:
        coin_id = coin.get("id")
        if not coin_id or coin_id in EXCLUDE_IDS:
            continue

        score, probability = evaluate_coin(coin)

        if score < 2 or probability < 65:
            log = f"⛔ {coin['symbol'].upper()}: score={score}, prob={probability}% — отклонена"
            ANALYSIS_LOG.append(log)
            continue

        coin["score"] = score
        coin["probability"] = probability
        candidates.append(coin)
        ANALYSIS_LOG.append(f"✅ {coin['symbol'].upper()}: score={score}, prob={probability}% — ДОБАВЛЕНА")

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
