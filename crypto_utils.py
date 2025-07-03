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

    # Расчёт оценки и сбор данных
    coin_data = []
    for coin in coins:
        price = coin.get('current_price')
        volume = coin.get('total_volume')
        change_24h = coin.get('price_change_percentage_24h_in_currency')
        change_7d = coin.get('price_change_percentage_7d_in_currency')
        name = coin['id']

        if price is None or volume is None or change_24h is None:
            continue

        # Считаем "сырую" перспективность
        score = 0
        score += change_24h * 0.6
        if change_7d is not None:
            score += change_7d * 0.2
        if volume > 1_000_000:
            score += 5
        if change_24h > 5:
            score += 3
        if change_24h < 0:
            score -= 4

        coin_data.append({
            'id': name,
            'price': round(price, 4),
            'change_24h': round(change_24h, 2),
            'change_7d': round(change_7d, 2) if change_7d else 0,
            'volume': int(volume),
            'raw_score': score
        })

    if not coin_data:
        return []

    # Нормализация вероятности (относительно лучших)
    max_score = max(c['raw_score'] for c in coin_data)
    min_score = min(c['raw_score'] for c in coin_data)

    for c in coin_data:
        if max_score == min_score:
            prob = 50
        else:
            prob = ((c['raw_score'] - min_score) / (max_score - min_score)) * 50 + 50
        c['probability'] = int(prob)

    # Отбор топ монет
    top_coins = sorted(coin_data, key=lambda x: x['probability'], reverse=True)[:top_n]

    return top_coins
