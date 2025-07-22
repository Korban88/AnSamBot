import math
import json
from crypto_list import TELEGRAM_WALLET_COIN_IDS
from crypto_utils import get_all_coin_data

REJECTION_LOG_FILE = "rejected_log.json"

def log_rejection(symbol, reason):
    try:
        with open(REJECTION_LOG_FILE, "r") as f:
            log = json.load(f)
    except FileNotFoundError:
        log = {}

    if symbol not in log:
        log[symbol] = []

    log[symbol].append(reason)

    with open(REJECTION_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def score_coin(coin):
    """
    Оценка монеты: чем выше, тем больше вероятность роста.
    """
    score = 0

    # Обрабатываем только подходящие монеты
    if coin.get("price_change_percentage_24h", 0) < -3:
        log_rejection(coin["symbol"], "Падение за 24ч > 3%")
        return 0

    if coin.get("rsi") is None:
        log_rejection(coin["symbol"], "Нет RSI")
        return 0

    if coin["rsi"] < 45:
        log_rejection(coin["symbol"], f"RSI < 45 ({coin['rsi']})")
        return 0

    # if coin.get("ma7") and coin["current_price"] < coin["ma7"]:
    #     log_rejection(coin["symbol"], "Цена ниже MA7")
    #     return 0

    # Чем выше рост за 24ч, тем лучше (но не слишком высокий)
    change_24h = coin.get("price_change_percentage_24h", 0)
    if 0 < change_24h < 5:
        score += change_24h

    # RSI 50–70 — зона возможного роста
    if 50 <= coin["rsi"] <= 70:
        score += 10
    elif 45 <= coin["rsi"] < 50:
        score += 5

    # Учитываем MA7, если есть
    if coin.get("ma7"):
        if coin["current_price"] > coin["ma7"]:
            score += 5
        else:
            score -= 3

    return round(score, 2)

def estimate_growth_probability(score):
    """
    Грубое приближение вероятности роста на основе балла
    """
    return min(95, max(40, int(60 + math.log1p(score) * 10)))

async def analyze_cryptos():
    coin_ids = list(TELEGRAM_WALLET_COIN_IDS.keys())
    data = await get_all_coin_data(coin_ids)

    results = []
    for coin in data:
        coin["score"] = score_coin(coin)
        if coin["score"] > 0:
            coin["probability"] = estimate_growth_probability(coin["score"])
            results.append(coin)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]
