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
        return data.get('prices', []), data.get('total_volumes', [])
    except:
        return [], []

def moving_average(prices, period=7):
    if len(prices) < period:
        return None
    close_prices = [p[1] for p in prices]
    return np.convolve(close_prices, np.ones(period)/period, mode='valid')

def rsi(prices, period=14):
    close_prices = [p[1] for p in prices]
    if len(close_prices) < period + 1:
        return None
    deltas = np.diff(close_prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period]) or 1e-9  # избегаем деления на 0
    rs = avg_gain / avg_loss
    rsi_values = [100 - (100 / (1 + rs))]
    for i in range(period, len(deltas)):
        gain = gains[i]
        loss = losses[i]
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period or 1e-9
        rs = avg_gain / avg_loss
        rsi_values.append(100 - (100 / (1 + rs)))
    return rsi_values[-1]

def volatility(prices):
    close_prices = [p[1] for p in prices]
    returns = np.diff(close_prices) / close_prices[:-1]
    return np.std(returns) * 100  # волатильность в %

def analyze_coin(coin_id):
    prices, volumes = get_historical_ohlc(coin_id)
    if not prices or len(prices) < 21:
        return None

    ma7 = moving_average(prices, 7)
    ma20 = moving_average(prices, 20)
    if ma7 is None or ma20 is None:
        return None

    rsi_val = rsi(prices, 14)
    if rsi_val is None:
        return None

    volat = volatility(prices)
    last_ma7 = ma7[-1]
    last_ma20 = ma20[-1]
    trend_score = 1 if last_ma7 > last_ma20 else -1

    # RSI оценка
    if rsi_val < 30:
        rsi_score = 1
    elif rsi_val > 70:
        rsi_score = -1
    else:
        rsi_score = 0

    # Объём
    last_volume = volumes[-1][1] if volumes else 0
    avg_volume = np.mean([v[1] for v in volumes[-7:]]) if volumes else 0
    volume_score = 1 if last_volume > avg_volume else -1

    # Волатильность
    vola_score = 1 if 2 < volat < 10 else 0  # слишком высокая волатильность считается минусом

    total_score = trend_score + rsi_score + volume_score + vola_score

    # Вероятность роста по итоговому скору
    base = 50
    probability = base + total_score * 10
    probability = max(5, min(95, probability))

    return {
        'probability': round(probability),
        'score': total_score,
        'rsi': round(rsi_val, 2),
        'ma7': round(last_ma7, 4),
        'ma20': round(last_ma20, 4),
        'volatility': round(volat, 2),
        'volume_7d_avg': round(avg_volume, 2),
        'volume_last': round(last_volume, 2)
    }
