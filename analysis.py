import logging
from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}  # исключаем стабильные и предсказуемые монеты

def evaluate_coin(coin):
    """
    Оценивает перспективность монеты и возвращает оценку (score) и вероятность роста.
    """
    rsi = coin.get("rsi", 0)
    ma7 = coin.get("ma7", 0)
    price = coin.get("current_price", 0)
    change_24h = coin.get("price_change_percentage_24h", 0)

    if not rsi or not ma7 or not price:
        return 0, 0

    score = 0

    # RSI фильтр (оптимальный диапазон: 45–65)
    if 45 <= rsi <= 65:
        score += 2
    elif 35 <= rsi < 45 or 65 < rsi <= 70:
        score += 1
    else:
        score -= 1

    # Цена выше MA7 — восходящий тренд
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
        score -= 3  # падение — исключаем

    # Простой расчёт вероятности роста
    probability = max(0, min(90, 60 + score * 5))
    return score, probability

async def analyze_cryptos():
    """
    Анализирует монеты из Telegram Wallet и возвращает топ-3 по вероятности роста.
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
            continue

        coin["score"] = score
        coin["probability"] = probability
        candidates.append(coin)

    # Сортируем по убыванию вероятности
    candidates.sort(key=lambda x: x["probability"], reverse=True)

    # Формируем финальный список из топ-3 монет
    top_signals = []
    for coin in candidates[:3]:
        price = coin["current_price"]
        target_price = round(price * 1.05, 4)
        stop_loss = round(price * 0.97, 4)
        change_24h = coin.get("price_change_percentage_24h", 0)

        signal = {
            "id": coin["id"],
            "symbol": coin["symbol"],
            "entry": price,
            "target": target_price,
            "stop_loss": stop_loss,
            "change_24h": round(change_24h, 2),
            "probability": coin["probability"]
        }
        top_signals.append(signal)

    return top_signals
