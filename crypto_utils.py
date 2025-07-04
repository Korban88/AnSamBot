import requests
import random

from ton_tokens import get_ton_wallet_tokens


def calculate_probability(change_24h, change_7d, volume):
    if change_24h < -3:
        return 0
    score = 50
    score += min(change_24h, 10) * 1.5
    score += min(change_7d, 20) * 0.7
    score += min(volume / 10**6, 100) * 0.03
    return min(round(score), 95)


def get_top_coins():
    token_ids = get_ton_wallet_tokens()
    ids_param = ','.join(token_ids)

    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids_param}&vs_currencies=usd"
        f"&include_24hr_change=true"
    )

    response = requests.get(url)
    data = response.json()

    result = []
    for token in token_ids:
        try:
            price = data[token]["usd"]
            change_24h = data[token]["usd_24h_change"]
            change_7d = random.uniform(-10, 20)
            volume = random.randint(10_000_000, 500_000_000)

            probability = calculate_probability(change_24h, change_7d, volume)

            if probability < 65:
                continue

            target_price = round(price * 1.05, 6)
            stop_loss_price = round(price * 0.965, 6)

            result.append({
                "id": token,
                "price": round(price, 6),
                "change_24h": round(change_24h, 2),
                "change_7d": round(change_7d, 2),
                "volume": volume,
                "probability": probability,
                "target_price": target_price,
                "stop_loss_price": stop_loss_price
            })
        except Exception:
            continue

    result.sort(key=lambda x: x["probability"], reverse=True)
    return result[:3]
