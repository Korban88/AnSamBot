from pycoingecko import CoinGeckoAPI
from ton_tokens import get_ton_wallet_tokens

cg = CoinGeckoAPI()

def get_top_ton_wallet_coins(top_n=3):
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
        ath = coin.get('ath')
        name = coin['id']

        # пропускаем монеты с плохими данными
        if price is None or volume is None or change_24h is None or ath is None:
            continue

        score = 0
        if change_24h > 0:
            score += 10
        if change_24h > 5:
            score += 10
        if change_7d and change_7d > 0:
            score += 10
        if volume > 10_000_000:
            score += 10
        if price < ath * 0.4:
            score += 10

        probability = min(90, 40 + score)  # диапазон 40%–90%

        scored_coins.append({
            'id': name,
            'price': round(price, 4),
            'change_24h': round(change_24h, 2),
            'change_7d': round(change_7d, 2) if change_7d is not None else 0,
            'volume': int(volume),
            'score': score,
            'probability': probability
        })

    sorted_coins = sorted(scored_coins, key=lambda c: c['score'], reverse=True)
    return sorted_coins[:top_n]
