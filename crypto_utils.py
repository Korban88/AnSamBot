from pycoingecko import CoinGeckoAPI
from ton_tokens import get_ton_wallet_tokens

cg = CoinGeckoAPI()

def get_top_coins(top_n: int = 3, min_probability: int = 60):
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

        score = 0
        # Анализ 24h динамики
        if change_24h > 0:
            score += 2
        if change_24h > 3:
            score += 2
        if change_24h > 5:
            score += 1
        if change_24h < -2:
            score -= 2
        if change_24h < -5:
            score -= 2

        # Анализ 7d тренда
        if change_7d is not None:
            if change_7d > 5:
                score += 2
            elif change_7d > 0:
                score += 1
            elif change_7d < -3:
                score -= 1

        # Объём торгов
        if volume > 100_000_000:
            score += 2
        elif volume > 10_000_000:
            score += 1
        elif volume < 1_000_000:
            score -= 1

        # Нормализация вероятности
        probability = min(100, max(20, score * 10))

        scored_coins.append({
            'id': name,
            'price': round(price, 4),
            'change_24h': round(change_24h, 2),
            'change_7d': round(change_7d, 2) if change_7d is not None else 0,
            'volume': int(volume),
            'score': score,
            'probability': probability,
            'target_price': round(price * 1.05, 4),
            'stop_loss_price': round(price * 0.965, 4)
        })

    filtered = [coin for coin in scored_coins if coin['probability'] >= min_probability]
    return sorted(filtered, key=lambda x: x['probability'], reverse=True)[:top_n] or sorted(scored_coins, key=lambda x: x['probability'], reverse=True)[:top_n]
