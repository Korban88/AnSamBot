import logging
from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}  # стабильные монеты

def evaluate_coin(coin):
    """
    Оценивает монету и возвращает (score, вероятность роста).
    """
    rsi = coin.get("rsi", 0)
    ma7 = coin.get("ma7", 0)
    price = coin.get("current_price", 0)
    change_24h = coin.get("price_change_percentage_24h", 0)

    if not rsi or not ma7 or not price:
        return 0, 0

    score = 0

    # RSI: зона силы — 45–65
    if 45 <= rsi <= 65:
        score += 2
    elif 35 <= rsi < 45 or 65 < rsi <= 70:
        score += 1
    else:
        score -= 1

    # MA7: восходящий тренд
    if price > ma7:
        score += 2
    else:
        score -= 1

    # 24ч изменение
    if change_24h > 5:
        score += 2
    elif change_24h > 2:
        score += 1
    elif change_24h < -3:
        score -= 3

    # Итоговая вероятность
    probability = max(0, min(90, 60 + score * 5))
    return score, probability

async def analyze_cryptos():
    """
    Возвращает топ-3 монеты по вероятности роста из списка Telegram Wallet.
    """
    coin_ids = TELEGRAM_WALLET_COIN_IDS if isinstance(TELEGRAM_WALLET_COIN_IDS, list) else list(TELEGRAM_WALLET_COIN_IDS.keys())
    all_data = await get_all_coin_data(coin_ids)

    candidates = []

    for coin in all_data:
        coin_id = coin.get("id")
        if not coin_id or coin_id in EXCLUDE_IDS:
            continue

        score, probability = evaluate_coin(coin)

        if score < 2 or probability < 65:
            logger.info(f"❌ Монета отклонена: {coin['symbol']}, score={score}, prob={probability}")
            continue

        coin["score"] = score
        coin["probability"] = probability
        candidates.append(coin)

    candidates.sort(key=lambda x: x["probability"], reverse=True)

    top_signals = []
    for coin in candidates[:3]:
        signal = {
            "id": coin["id"],
            "symbol": coin["symbol"],
            "current_price": coin["current_price"],
            "price_change_percentage_24h": round(coin.get("price_change_percentage_24h", 0), 2),
            "probability": coin["probability"]
        }
        top_signals.append(signal)

    return top_signals
