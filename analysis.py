import logging
from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}
ANALYSIS_LOG = []

def evaluate_coin(coin):
    rsi = coin.get("rsi", 0)
    ma7 = coin.get("ma7", 0)
    price = coin.get("current_price", 0)
    change_24h = coin.get("price_change_percentage_24h", 0)
    volume = coin.get("total_volume", 0)
    symbol = coin.get("symbol", "?").upper()

    reasons = []
    score = 0

    if 52 <= rsi <= 60:
        score += 1
    else:
        reasons.append(f"RSI {rsi} вне диапазона 52–60")

    if price > ma7:
        score += 1
    else:
        reasons.append(f"Цена ${price} ниже MA7 ${ma7}")

    if change_24h >= 2.5:
        score += 1
    else:
        reasons.append(f"Изменение за 24ч {change_24h}% недостаточно")

    if 5_000_000 <= volume <= 100_000_000:
        score += 1
    else:
        reasons.append(f"Объём {volume} вне диапазона 5M–100M")

    # Улучшенный расчёт вероятности
    rsi_weight = 1 if 52 <= rsi <= 60 else 0
    ma_weight = 1 if price > ma7 else 0
    change_weight = min(change_24h / 5, 1)
    volume_weight = 1 if 5_000_000 <= volume <= 100_000_000 else 0

    prob = 50 + (rsi_weight + ma_weight + change_weight + volume_weight) * 11.25
    prob = round(min(prob, 95), 2)

    if score >= 4:
        ANALYSIS_LOG.append(f"✅ {symbol}: score={score}, prob={prob}%")
    else:
        ANALYSIS_LOG.append(f"❌ {symbol}: отклонено — {', '.join(reasons)}")

    return score, prob


async def analyze_cryptos(fallback=False):
    global ANALYSIS_LOG
    ANALYSIS_LOG.clear()

    coin_ids = TELEGRAM_WALLET_COIN_IDS if isinstance(TELEGRAM_WALLET_COIN_IDS, list) else list(TELEGRAM_WALLET_COIN_IDS.keys())
    all_data = await get_all_coin_data(coin_ids)

    candidates = []

    for coin in all_data:
        if coin.get("id") in EXCLUDE_IDS:
            continue
        score, prob = evaluate_coin(coin)
        if score >= 4:
            coin["score"] = score
            coin["probability"] = prob
            candidates.append(coin)

    candidates.sort(key=lambda x: (x["probability"], x["price_change_percentage_24h"]), reverse=True)

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
        logger.info("⚠️ Нет подходящих монет вообще.")

    return top_signals
