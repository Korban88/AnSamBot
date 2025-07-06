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
    return min(95, 50 + score * 15)

async def analyze_cryptos(coin_data):
    results = []

    for coin in CRYPTO_LIST:
        coin_id = coin["id"]
        symbol = coin["symbol"]

        data = coin_data.get(coin_id)
        if not isinstance(data, dict):
            continue  # пропускаем, если данные повреждены

        price = data.get("price")
        change_24h = data.get("change_24h")
        ma = await get_moving_average(coin_id)
        rsi = await get_rsi(coin_id)

        if any(metric is None for metric in [price, ma, rsi, change_24h]):
            continue

        probability = calculate_probability(change_24h, rsi, ma, price)

        entry_price = price
        target_price = round(price * 1.05, 4)
        stop_loss = round(price * 0.97, 4)

        results.append({
            "id": coin_id,
            "symbol": symbol,
            "price": price,
            "ma": ma,
            "rsi": rsi,
            "change_24h": change_24h,
            "probability": probability,
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss
        })

    filtered = [r for r in results if r["probability"] >= 60 and r["change_24h"] > -6]
    sorted_results = sorted(filtered, key=lambda x: x["probability"], reverse=True)
    return sorted_results[:3]
