from analysis import analyze_coin
from crypto_utils import get_top_coins

# Порог вероятности для фильтра
MIN_PROBABILITY = 65
MAX_DROP_24H = -3.0

def generate_signal(return_top3=False):
    coins = get_top_coins()
    candidates = []

    for coin in coins:
        try:
            metrics = analyze_coin(coin["id"])
            if not metrics:
                continue

            prob = metrics["probability"]
            change = coin["price_change_percentage_24h"]

            if prob >= MIN_PROBABILITY and change > MAX_DROP_24H:
                candidates.append({
                    "name": coin["name"],
                    "symbol": coin["symbol"],
                    "price": coin["current_price"],
                    "change_24h": change,
                    "rsi": metrics["rsi"],
                    "ma7": metrics["ma7"],
                    "ma20": metrics["ma20"],
                    "score": metrics["score"],
                    "probability": prob,
                    "entry": round(coin["current_price"], 4),
                    "target": round(coin["current_price"] * 1.05, 4),
                    "stop": round(coin["current_price"] * 0.965, 4),
                })
        except Exception:
            continue

    candidates.sort(key=lambda x: (x["probability"], x["score"], x["change_24h"]), reverse=True)

    if return_top3:
        return candidates[:3]

    return candidates[0] if candidates else None
