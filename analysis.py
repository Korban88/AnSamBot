import json
import os
from datetime import datetime
from crypto_utils import get_current_prices, load_indicators_cache, get_cached_indicator, set_cached_indicator, save_indicators_cache

# Стейблкоины, которые исключаются из анализа
STABLECOINS = {
    "tether", "usd-coin", "binance-usd", "true-usd", "usdd", "usdp", "paxos-standard", "gemini-dollar", "husd"
}

TOP_SIGNALS_CACHE_FILE = "top_signals_cache.json"

# Расчёт score на основе множества факторов
def calculate_score(rsi, ma_diff, change_24h, volume):
    score = 0
    if 45 <= rsi <= 65:
        score += 2
    if ma_diff > 0:
        score += 2
    if change_24h > 0:
        score += 2
    if volume > 1000000:
        score += 1
    return score


def estimate_growth_probability(score):
    # Конвертация score в вероятность роста
    return min(round(50 + score * 6, 2), 100.0)


async def analyze_cryptos(crypto_list):
    # Исключаем стейблкоины
    filtered = [c for c in crypto_list if c.lower() not in STABLECOINS]

    # Загружаем кэш индикаторов
    cache = load_indicators_cache()

    # Получаем текущие цены и 24h изменения
    prices_data = await get_current_prices(filtered)

    results = []
    for coin in filtered:
        data = prices_data.get(coin)
        if not data or "usd" not in data:
            continue

        current_price = data["usd"]
        change_24h = data.get("usd_24h_change", 0)

        # Получаем индикаторы из кэша
        rsi = get_cached_indicator(cache, coin, "rsi")
        ma = get_cached_indicator(cache, coin, "ma")
        volume = get_cached_indicator(cache, coin, "volume")

        # Если чего-то нет — пропускаем
        if None in (rsi, ma, volume):
            continue

        ma_diff = current_price - ma
        score = calculate_score(rsi, ma_diff, change_24h, volume)
        probability = estimate_growth_probability(score)

        results.append({
            "coin": coin,
            "price": round(current_price, 6),
            "rsi": rsi,
            "ma": ma,
            "volume": volume,
            "change_24h": round(change_24h, 2),
            "score": score,
            "probability": probability
        })

    # Сохраняем кэш обратно
    save_indicators_cache(cache)

    # Отбираем top-3 монеты по score
    top_signals = sorted(results, key=lambda x: x["score"], reverse=True)[:3]

    # Сохраняем кеш топа
    with open(TOP_SIGNALS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(top_signals, f, ensure_ascii=False, indent=2)

    return top_signals


def load_top_signals_cache():
    if os.path.exists(TOP_SIGNALS_CACHE_FILE):
        with open(TOP_SIGNALS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def get_next_signal_from_cache():
    top_signals = load_top_signals_cache()

    if not top_signals:
        return None

    # Ротация: первый сигнал перемещается в конец
    signal = top_signals.pop(0)
    top_signals.append(signal)

    with open(TOP_SIGNALS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(top_signals, f, ensure_ascii=False, indent=2)

    return signal
