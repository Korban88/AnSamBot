import json
from crypto_utils import get_market_data
from crypto_list import CRYPTO_LIST

def calculate_score(data):
    if not data:
        return 0

    score = 0

    # RSI: чем ближе к 30, тем лучше для покупки
    rsi = data.get("rsi")
    if rsi is not None:
        if rsi < 30:
            score += 3
        elif rsi < 50:
            score += 2
        elif rsi < 70:
            score += 1

    # Moving Average: если цена ниже MA, считается недооцененной
    current_price = data.get("current_price")
    ma = data.get("ma")
    if ma and current_price and current_price < ma:
        score += 2

    # Рост за 24ч — не более 3% (иначе считаем монету уже "улетевшей")
    change_24h = data.get("change_24h")
    if change_24h is not None and change_24h > -3:
        score += 1

    # Объем торгов
    volume = data.get("volume")
    if volume and volume > 500_000:
        score += 1

    return score


async def get_top_signal():
    all_data = await get_market_data(CRYPTO_LIST)
    if not all_data:
        return None

    scored = []
    for coin, data in all_data.items():
        change = data.get("change_24h", 0)
        if change < -3:  # фильтр падения за сутки
            continue
        score = calculate_score(data)
        scored.append((coin, score, data))

    if not scored:
        return None

    # Сортируем по score (высший приоритет)
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[0]
    coin, score, data = top

    # Оценка вероятности роста: привязана к максимальному score
    max_score = 7
    probability = round((score / max_score) * 100)

    current_price = data.get("current_price")
    change_24h = data.get("change_24h", 0)
    stop_loss = round(current_price * 0.97, 4)
    take_profit = round(current_price * 1.05, 4)

    signal = (
        f"*💡 Сигнал на покупку: {coin.upper()}*\n"
        f"*Текущая цена:* {current_price:.4f} USDT\n"
        f"*Цель:* {take_profit:.4f} USDT (+5%)\n"
        f"*Стоп-лосс:* {stop_loss:.4f} USDT (-3%)\n"
        f"*Изменение за 24ч:* {change_24h:.2f}%\n"
        f"*Вероятность роста:* {probability}%"
    )
    return signal
