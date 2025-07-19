import json
import os
import aiohttp
import asyncio
import math
from crypto_list import CRYPTO_LIST
from crypto_utils import get_current_prices

CACHE_FILE = "top_signals_cache.json"

def is_valid_price(price):
    try:
        return isinstance(price, (int, float)) and price > 0 and not math.isnan(price)
    except:
        return False

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

        if not price_data:
            continue

        entry_price = price_data.get("usd")
        change_24h = price_data.get("usd_24h_change")

        if not is_valid_price(entry_price) or not isinstance(change_24h, (float, int)):
            print(f"Пропущено: {coin_name} — некорректная цена ({entry_price}) или изменение ({change_24h})")
            continue

        if change_24h < -3:
            print(f"Пропущено: {coin_name} — падение за 24ч: {change_24h:.2f}%")
            continue

        score = max(0, min(1, 0.7 + (0.03 - abs(change_24h) / 100)))
        probability = round(score * 100, 2)

        top_signals.append({
            "id": coin_id,
            "name": coin_name,
            "entry_price": round(entry_price, 4),
            "target_price": round(entry_price * 1.05, 4),
            "stop_loss": round(entry_price * 0.97, 4),
            "probability": probability
        })

    top_signals.sort(key=lambda x: x["probability"], reverse=True)
    top_signals = top_signals[:3]

    if top_signals:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"top_signals": top_signals}, f, ensure_ascii=False, indent=2)

        print(f"Топ монет сформирован: {[s['name'] for s in top_signals]}")
    else:
        print("Нет подходящих монет для сигнала.")

    return top_signals
