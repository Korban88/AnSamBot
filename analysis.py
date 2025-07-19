import json
import os
from crypto_list import CRYPTO_LIST
from crypto_utils import get_current_prices

CACHE_FILE = "top_signals_cache.json"


async def get_top_signals():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached = json.load(f)
            if cached.get("top_signals"):
                return cached["top_signals"]

    print("Анализируем монеты...")

    prices = await get_current_prices([coin["id"] for coin in CRYPTO_LIST])
    top_signal = None
    top_score = -1

    for coin in CRYPTO_LIST:
        coin_id = coin["id"]
        coin_name = coin["name"]
        price_data = prices.get(coin_id)

        if not price_data or not price_data.get("usd"):
            continue

        current_price = price_data["usd"]
        change_24h = price_data.get("usd_24h_change", 0)

        if change_24h < -3:
            continue

        # Строгая формула оценки
        score = 0
        if 0 < change_24h < 5:
            score += 0.3
        if change_24h > 0:
            score += 0.2
        if current_price > 0:
            score += 0.2
        score += max(0, min(0.3, (5 - abs(change_24h)) / 10))

        if score > top_score:
            top_score = score
            top_signal = {
                "id": coin_id,
                "name": coin_name,
                "entry_price": round(current_price, 4),
                "target_price": round(current_price * 1.05, 4),
                "stop_loss": round(current_price * 0.97, 4),
                "change_24h": round(change_24h, 2),
                "probability": round(score * 100, 2)
            }

    result = [top_signal] if top_signal else []

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({"top_signals": result}, f, ensure_ascii=False, indent=2)

    print(f"Сигнал: {top_signal['name'] if top_signal else 'нет подходящих монет'}")
    return result
