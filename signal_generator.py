from analysis import analyze_coin
from crypto_utils import get_top_coins

MIN_PROBABILITY = 65
MAX_DROP_24H = -3.0

def generate_signal(return_top3=False):
    coins = get_top_coins()
    analyzed = []

    for coin in coins:
        try:
            metrics = analyze_coin(coin["id"])
            if not metrics:
                continue

            if metrics["probability"] >= MIN_PROBABILITY and coin["price_change_percentage_24h"] > MAX_DROP_24H:
                analyzed.append({
                    "id": coin["id"],
                    "symbol": coin["symbol"],
                    "name": coin["name"],
                    "price": coin["current_price"],
                    "change_24h": coin["price_change_percentage_24h"],
                    "probability": metrics["probability"],
                    "rsi": metrics["rsi"],
                    "ma7": metrics["ma7"],
                    "ma20": metrics["ma20"],
                    "score": metrics["score"]
                })
        except Exception:
            continue

    if not analyzed:
        return None

    analyzed.sort(key=lambda x: (x["probability"], x["change_24h"]), reverse=True)

    top3 = analyzed[:3]
    for coin in top3:
        coin["entry"] = round(coin["price"], 4)
        coin["target"] = round(coin["price"] * 1.05, 4)
        coin["stop"] = round(coin["price"] * 0.965, 4)

    if return_top3:
        return top3
    return top3[0]
