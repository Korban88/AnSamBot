import asyncio
from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

# Настройки фильтрации
MIN_VOLUME_USD = 1000000
MAX_24H_DROP = -3.0
MIN_RSI = 35
MAX_RSI = 70

def calculate_growth_score(coin):
    """
    Расчёт скоринга перспективности монеты на основе ряда метрик:
    - RSI
    - Изменение цены за 24 часа
    - Рост объёма
    - Волатильность (разница high - low)
    """
    change_24h = coin.get("price_change_percentage_24h", 0)
    volume = coin.get("total_volume", 0)
    rsi = coin.get("rsi", 0)
    ma_7 = coin.get("ma7", 0)
    current_price = coin.get("current_price", 0)
    high_24h = coin.get("high_24h", 0)
    low_24h = coin.get("low_24h", 0)

    if not current_price or not high_24h or not low_24h:
        return 0

    volatility_score = (high_24h - low_24h) / current_price
    rsi_score = 1 - abs(50 - rsi) / 50  # лучше, когда ближе к 50
    change_score = max(0, change_24h / 5)  # лучше, когда рост
    volume_score = min(volume / 1e7, 1)  # выше объем — выше шанс всплеска
    trend_score = 1 if current_price > ma_7 else 0

    score = (volatility_score * 0.3 +
             rsi_score * 0.25 +
             change_score * 0.2 +
             volume_score * 0.15 +
             trend_score * 0.1)

    return round(score, 4)

def calculate_growth_probability(score):
    """
    Преобразование скоринга в вероятность роста
    """
    if score > 0.75:
        return 90 + (score - 0.75) * 100  # до 100%
    elif score > 0.6:
        return 75 + (score - 0.6) * 100
    elif score > 0.5:
        return 65 + (score - 0.5) * 100
    else:
        return 0

async def analyze_cryptos():
    """
    Основная функция анализа монет и возврата топ-3 с наибольшей вероятностью роста
    """
    coins_data = await get_all_coin_data(TELEGRAM_WALLET_COIN_IDS)

    candidates = []
    for coin in coins_data:
        if not coin:
            continue

        change_24h = coin.get("price_change_percentage_24h", 0)
        volume = coin.get("total_volume", 0)
        rsi = coin.get("rsi", 0)

        if change_24h < MAX_24H_DROP:
            continue
        if volume < MIN_VOLUME_USD:
            continue
        if rsi < MIN_RSI or rsi > MAX_RSI:
            continue

        score = calculate_growth_score(coin)
        probability = calculate_growth_probability(score)

        if probability >= 65:
            coin["score"] = score
            coin["probability"] = round(probability)
            candidates.append(coin)

    sorted_coins = sorted(candidates, key=lambda x: x["probability"], reverse=True)
    return sorted_coins[:3]

def get_top_signal():
    """
    Синхронная обёртка для получения лучшего сигнала (монеты с максимальной вероятностью роста)
    """
    loop = asyncio.get_event_loop()
    top_signals = loop.run_until_complete(analyze_cryptos())
    return top_signals[0] if top_signals else None
