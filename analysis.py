import json
import os
import aiohttp
import asyncio
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
    top_signals = []

    for coin in CRYPTO_LIST:
        coin_id = coin["id"]
        coin_name = coin["name"]
        price_data = prices.get(coin_id)

        if not price_data or not price_data.get("usd"):
            continue

        entry_price = price_data["usd"]
        change_24h = price_data.get("usd_24h_change", 0)

        # Пример фильтра и оценки
        if change_24h < -3:
            continue

        score = max(0, min(1, 0.7 + (0.03 - abs(change_24h) / 100)))  # Условная логика

        top_signals.append({
            "id": coin_id,
            "name": coin_name,
            "entry_price": round(entry_price, 4),
            "target_price": round(entry_price * 1.05, 4),
            "stop_loss": round(entry_price * 0.97, 4),
            "probability": round(score * 100, 2)  # Гарантированное добавление probability
        })

    # Сортировка по probability
    top_signals.sort(key=lambda x: x["probability"], reverse=True)
    top_signals = top_signals[:3]

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({"top_signals": top_signals}, f, ensure_ascii=False, indent=2)

    print(f"Топ монет сформирован: {[s['name'] for s in top_signals]}")
    return top_signals
