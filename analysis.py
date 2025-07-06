from crypto_utils import get_rsi, get_moving_average
from config import TELEGRAM_WALLET_COINS

def calculate_probability(score):
    if score >= 8:
        return 90.0
    elif score >= 7:
        return 80.0
    elif score >= 6:
        return 70.0
    elif score >= 5:
        return 60.0
    elif score >= 4:
        return 55.0
    else:
        return 0.0

async def analyze_cryptos(coin_data):
    results = []

    for coin in TELEGRAM_WALLET_COINS:
        coin_id = coin["id"]
        symbol = coin["symbol"]
        data = coin_data.get(coin_id)
        if not data:
            continue

        try:
            price = data["market_data"]["current_price"]["usd"]
            change_24h = data["market_data"]["price_change_percentage_24h"]
            if change_24h is None:
                change_24h = 0.0

            rsi = get_rsi(data)
            ma = get_moving_average(data)

            score = 0

            if rsi < 70:
                score += 1
            if rsi < 60:
                score += 1
            if rsi < 50:
                score += 1
            if change_24h > -2.0:
                score += 1
            if change_24h > 0.0:
                score += 1
            if price > ma:
                score += 1

            probability = calculate_probability(score)
            if probability < 55.0:
                continue  # отсекаем слабые монеты

            entry_price = price
            target_price = price * 1.05
            stop_loss = price * 0.97

            results.append({
                "id": coin_id,
                "symbol": symbol,
                "score": score,
                "probability": probability,
                "entry_price": entry_price,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "rsi": rsi,
                "ma": ma,
                "change_24h": change_24h
            })

        except Exception:
            continue

    # Сортировка по вероятности
    results.sort(key=lambda x: x["probability"], reverse=True)
    return results[:3]
