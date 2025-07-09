# analysis.py

from crypto_list import TELEGRAM_WALLET_CRYPTOS
from crypto_utils import get_current_price, get_24h_change, get_rsi, get_ma
from config import MAX_PRICE_DROP_24H, MIN_GROWTH_PROBABILITY, TOP3_CACHE_FILE
import json
import os
import time

def save_top3_cache(top3):
    cache = {
        "timestamp": int(time.time()),
        "top3": top3
    }
    with open(TOP3_CACHE_FILE, "w") as f:
        json.dump(cache, f)

def load_top3_cache(max_age_seconds=3600):
    if not os.path.exists(TOP3_CACHE_FILE):
        return []

    with open(TOP3_CACHE_FILE, "r") as f:
        data = json.load(f)

    now = int(time.time())
    if now - data.get("timestamp", 0) > max_age_seconds:
        return []

    return data.get("top3", [])

def analyze_cryptos():
    scored_cryptos = []
    diagnostics = []

    for coin_id in TELEGRAM_WALLET_CRYPTOS:
        price = get_current_price(coin_id)
        change_24h = get_24h_change(coin_id)
        rsi = get_rsi(coin_id)
        ma = get_ma(coin_id)

        if None in (price, change_24h, rsi, ma):
            diagnostics.append(f"🔴 {coin_id} — недоступны данные")
            continue

        if change_24h < MAX_PRICE_DROP_24H:
            diagnostics.append(f"⚠️ {coin_id} — падение {change_24h:.2f}% за 24ч")
            continue

        score = 0

        # RSI: чем ниже, тем лучше
        if rsi < 30:
            score += 30
        elif rsi < 40:
            score += 20
        elif rsi < 50:
            score += 10

        # Скользящая средняя
        if price > ma:
            score += 25

        # Изменение за 24ч
        if change_24h > 0:
            score += 15
        elif -1 <= change_24h <= 0:
            score += 5

        # Масштабирование по цене
        if price > 1:
            score += min(price ** 0.2, 10)

        # Перевод в вероятность
        probability = round(min(95.0, max(35.0, score)), 1)

        if probability >= MIN_GROWTH_PROBABILITY:
            scored_cryptos.append({
                "id": coin_id,
                "price": price,
                "change_24h": change_24h,
                "rsi": rsi,
                "ma": ma,
                "score": score,
                "probability": probability
            })
        else:
            diagnostics.append(f"⚪ {coin_id} — низкая вероятность: {probability}%")

    if not scored_cryptos:
        # Для вывода диагностики в Telegram
        scored_cryptos.append({
            "id": "diagnostics",
            "details": diagnostics
        })

    top_3 = sorted(
        [c for c in scored_cryptos if c["id"] != "diagnostics"],
        key=lambda x: x["probability"],
        reverse=True
    )[:3]

    if not top_3 and diagnostics:
        print("🔍 Диагностика анализа монет:")
        for msg in diagnostics:
            print(msg)

    save_top3_cache(top_3)
    return top_3
