from pycoingecko import CoinGeckoAPI
from ton_tokens import get_ton_wallet_tokens
import requests
import numpy as np
import math

cg = CoinGeckoAPI()

def get_historical_ohlc(coin_id, days=30, vs_currency='usd'):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily'
    }
    response = requests.get(url, params=params)
    data = response.json()
    prices = data.get('prices', [])
    return prices  # список [ [timestamp, price], ... ]

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
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
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

    trend_score = 1 if last_ma7 > last_ma20 else -1

    if rsi_value < 30:
        rsi_score = 1
    elif rsi_value > 70:
        rsi_score = -1
    else:
        rsi_score = 0

    score = trend_score + rsi_score

    probability = 50 + score * 25
    probability = max(0, min(100, probability))

    return {
        'probability': probability,
        'ma7': round(last_ma7, 4),
        'ma20': round(last_ma20, 4),
        'rsi': round(rsi_value, 2),
        'score': score
    }

def calculate_probability(change_24h, change_7d, volume, price):
    if change_24h is None or volume is None:
        return 0

    weight_24h = 0.5
    weight_7d = 0.3
    weight_volume = 0.1
    weight_price = 0.1

    score_24h = max(-10, min(10, change_24h)) / 10
    score_7d = max(-15, min(15, change_7d or 0)) / 15
    score_volume = min(1, math.log10(volume + 1) / 10)
    score_price = 1 - min(1, math.log10(price + 1) / 3)

    score = (
        score_24h * weight_24h +
        score_7d * weight_7d +
        score_volume * weight_volume +
        score_price * weight_price
    )

    probability = round(max(0, min(1, score)) * 100)
    return probability

def get_top_coins(top_n: int = 3, min_probability: int = 70):
    coin_ids = get_ton_wallet_tokens()
    if not coin_ids:
        return []

    coins = cg.get_coins_markets(
        vs_currency='usd',
        ids=coin_ids,
        order='market_cap_desc',
        per_page=250,
        price_change_percentage='24h,7d'
    )

    scored_coins = []

    for coin in coins:
        price = coin.get('current_price')
        volume = coin.get('total_volume')
        change_24h = coin.get('price_change_percentage_24h_in_currency')
        change_7d = coin.get('price_change_percentage_7d_in_currency')
        name = coin['id']

        if price is None or volume is None or change_24h is None:
            continue

        base_probability = calculate_probability(change_24h, change_7d, volume, price)
        tech_data = analyze_coin(name)

        if tech_data:
            combined_prob = round((base_probability + tech_data['probability']) / 2)
        else:
            combined_prob = base_probability

        scored_coins.append({
            'id': name,
            'price': round(price, 4),
            'change_24h': round(change_24h, 2),
            'change_7d': round(change_7d, 2) if change_7d is not None else 0,
            'volume': int(volume),
            'probability': combined_prob,
            'target_price': round(price * 1.05, 4),
            'stop_loss_price': round(price * 0.965, 4)
        })

    filtered = [coin for coin in scored_coins if coin['probability'] >= min_probability]

    return sorted(filtered, key=lambda x: x['probability'], reverse=True)[:top_n] or \
           sorted(scored_coins, key=lambda x: x['probability'], reverse=True)[:top_n]
