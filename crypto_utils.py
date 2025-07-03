from pycoingecko import CoinGeckoAPI
from ton_tokens import get_ton_wallet_tokens

cg = CoinGeckoAPI()

def get_top_ton_wallet_coins(top_n=1, randomize=False):
    coin_ids = get_ton_wallet_tokens()

    if not coin_ids:
        return None

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

        score = 0
        if change_24h > 0:
            score += 2
        if change_7d is not None and change_7d > 0:
            score += 1
        if volume > 1_000_000:
            score += 1
        if change_24h > 3:
            score += 1
        if change_24h > 5:
            score += 1
        if change_24h < -1:
            score -= 2

        scored_coins.append({
            'id': name,
            'price': round(price, 4),
            'change_24h': round(change_24h, 2),
            'change_7d': round(change_7d, 2) if change_7d is not None else 0,
            'volume': int(volume),
            'score': score
        })

    if not scored_coins:
        return None

    # Сортировка по score
    sorted_coins = sorted(scored_coins, key=lambda x: x['score'], reverse=True)

    if randomize:
        import random
        return [random.choice(sorted_coins[:top_n])]

    return sorted_coins[:top_n]
