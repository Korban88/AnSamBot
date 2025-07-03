from pycoingecko import CoinGeckoAPI
from ton_tokens import get_ton_wallet_tokens
import math

cg = CoinGeckoAPI()

def calculate_probability(change_24h, change_7d, volume, price):
    if change_24h is None or volume is None:
        return 0

    # Факторы влияния
    weight_24h = 0.5
    weight_7d = 0.3
    weight_volume = 0.1
    weight_price = 0.1

    # Стандартизация
    score_24h = max(-10, min(10, change_24h)) / 10  # от -1 до 1
    score_7d = max(-15, min(15, change_7d or 0)) / 15  # от -1 до 1
    score_volume = min(1, math.log10(volume + 1) / 10)  # от 0 до ~1
    score_price = 1 - min(1, math.log10(price + 1) / 3)  # дешёвые выше

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

        probability = calculate_probability(change_24h, change_7d, volume, price)

        scored_coins.append({
            'id': name,
            'price': round(price, 4),
            'change_24h': round(change_24h, 2),
            'change_7d': round(change_7d, 2) if change_7d is not None else 0,
            'volume': int(volume),
            'probability': probability,
            'target_price': round(price * 1.05, 4),
            'stop_loss_price': round(price * 0.965, 4)
        })

    filtered = [coin for coin in scored_coins if coin['probability'] >= min_probability]

    return sorted(filtered, key=lambda x: x['probability'], reverse=True)[:top_n] or \
           sorted(scored_coins, key=lambda x: x['probability'], reverse=True)[:top_n]
