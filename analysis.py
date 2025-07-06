import statistics
from crypto_utils import get_current_price, get_moving_average, get_rsi
from crypto_list import CRYPTO_LIST

def calculate_probability(change_24h, rsi, ma, price):
    score = 0

    if change_24h > 0:
        score += 1
    if rsi < 70:
        score += 1
    if price > ma:
        score += 1

    probability = min(95, 50 + score * 15)
    return probability

async def analyze_cryptos(coin_data):
    results = []

    for coin in crypto_list:
        coin_id = coin["id"]
        symbol = coin["symbol"]

        data = coin_data.get(coin_id)
        if not data:
            continue

        price = data["price"]
        ma = await get_moving_average(coin_id)
        rsi = await get_rsi(coin_id)
        change_24h = data["change_24h"]

        if any(metric is None for metric in [price, ma, rsi, change_24h]):
            continue

        probability = calculate_probability(change_24h, rsi, ma, price)

        results.append({
            "id": coin_id,
            "symbol": symbol,
            "price": price,
            "ma": ma,
            "rsi": rsi,
            "change_24h": change_24h,
            "probability": probability
        })

    # Ослабленный фильтр: пропускаем монеты с вероятностью >= 60% (было 65%) и падением не более -6% (было -3%)
    filtered = [
        r for r in results
        if r["probability"] >= 60 and r["change_24h"] > -6
    ]

    sorted_results = sorted(filtered, key=lambda x: x["probability"], reverse=True)
    return sorted_results[:3]
