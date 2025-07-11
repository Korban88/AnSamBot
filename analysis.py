from crypto_utils import get_current_price, get_24h_change, get_rsi, get_ma, load_indicators
from config import MIN_GROWTH_PROBABILITY, TARGET_PROFIT_PERCENT, MAX_PRICE_DROP_24H


def analyze_cryptos():
    indicators = load_indicators()
    result = []
    for coin_id, data in indicators.items():
        if not data.get("price") or not data.get("change_24h"):
            print(f"🔴 {coin_id} — недоступны данные")
            continue
        score = 50 + data.get("change_24h", 0) * 2
        probability = max(min(score, 100), 0)
        if probability >= MIN_GROWTH_PROBABILITY and data.get("change_24h") >= MAX_PRICE_DROP_24H:
            result.append({
                "id": coin_id,
                "price": data["price"],
                "change_24h": round(data["change_24h"], 2),
                "growth_probability": round(probability, 2),
                "target_percent": TARGET_PROFIT_PERCENT,
                "stop_loss_percent": round(MAX_PRICE_DROP_24H, 2)
            })
    result.sort(key=lambda x: x["growth_probability"], reverse=True)
    return result[:3]
