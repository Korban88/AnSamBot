from pycoingecko import CoinGeckoAPI
from ton_tokens import get_ton_wallet_tokens

cg = CoinGeckoAPI()

def get_top_ton_wallet_coins():
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

    best_coin = None
    best_score = -999

    for coin in coins:
        price = coin['current_price']
        volume = coin['total_volume']
        change_24h = coin.get('price_change_percentage_24h_in_currency', 0)
        change_7d = coin.get('price_change_percentage_7d_in_currency', 0)
        name = coin['id']

        score = 0
        if change_24h > 0:
            score += 2
        if change_7d > 0:
            score += 1
        if volume > 1_000_000:
            score += 1
        if change_24h > 3:
            score += 1
        if change_24h > 5:
            score += 1
        if change_24h < -1:
            score -= 2

        if score > best_score:
            best_score = score
            best_coin = {
                'id': name,
                'price': round(price, 4),
                'change_24h': round(change_24h, 2),
                'change_7d': round(change_7d, 2),
                'volume': int(volume),
                'score': score
            }

    return best_coin
