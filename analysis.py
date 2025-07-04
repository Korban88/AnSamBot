import requests
import numpy as np

def get_historical_ohlc(coin_id, days=30, vs_currency='usd'):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get('prices', [])  # [[timestamp, price], ...]
    except:
        return []

def moving_average(prices, period=7):
    if len(prices) < period:
        return None
    close_prices = [p[1] for p in prices]
    ma = np.convolve(close_prices, np.ones(period)/period, mode='valid')
    return ma

def rsi(prices, period=14):
    close_prices = [p[1] for p in prices]
    if len(close_prices) < period + 1:
        return None
    deltas = np.diff(close_prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi_values = [100 - (100 / (1 + rs))]
    for i in range(period, len(deltas)):
        gain = gains[i]
        loss = losses[i]
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi_values.append(100 - (100 / (1 + rs)))
    return rsi_values[-1]

def analyze_coin(coin_id):
    prices = get_historical_ohlc(coin_id)
    if not prices or len(prices) < 20:
        return None

    ma7 = moving_average(prices, 7)
    ma20 = moving_average(prices, 20)
    if ma7 is None or ma20 is None:
        return None

    rsi_value = rsi(prices, 14)
    if rsi_value is None:
        return None

    last_ma7 = ma7[-1]
    last_ma20 = ma20[-1]

    # Тренд
    trend_score = 1 if last_ma7 > last_ma20 else -1

    # RSI
    if rsi_value < 30:
        rsi_score = 1
    elif rsi_value > 70:
        rsi_score = -1
    else:
        rsi_score = 0

    score = trend_score + rsi_score

    # Вероятность роста
    probability = 50 + score * 25
    probability = max(0, min(100, probability))

    return {
        'probability': int(probability),
        'ma7': round(last_ma7, 4),
        'ma20': round(last_ma20, 4),
        'rsi': round(rsi_value, 2),
        'score': score
    }
