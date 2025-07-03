from pycoingecko import CoinGeckoAPI
from ton_tokens import get_ton_wallet_tokens

cg = CoinGeckoAPI()

def get_top_coins(top_n: int = 3, min_probability: int = 70):
    coin_ids = get_ton_wallet_tokens()
    if not coin_ids:
        return []

    try:
        coins = cg.get_coins_markets(
            vs_currency='usd',
            ids=coin_ids,
            order='market_cap_desc',
            per_page=250,
            price_change_percentage='24h,7d'
        )
    except Exception as e:
        print(f"Ошибка получения данных CoinGecko: {e}")
        return []

    scored_coins = []

    for coin in coins:
        price = coin.get('current_price')
        volume = coin.get('total_volume')
        change_24h = coin.get('price_change_percentage_24h_in_currency')
        change_7d = coin.get('price_change_percentage_7d_in_currency')
        name = coin.get('id')

        if price is None or volume is None or change_24h is None:
            continue

        score = 0

        # Баллы за положительный тренд
        if change_24h > 0:
            score += 2
        if change_7d is not None and change_7d > 0:
            score += 1

        # Баллы за высокие объемы — чем выше, тем лучше
        if volume > 1_000_000:
            score += 1

        # Баллы за сильный рост за сутки
        if change_24h > 3:
            score += 1
        if change_24h > 5:
            score += 1

        # Баллы за падение — штраф
        if change_24h < -1:
            score -= 2

        # Расчет вероятности на основе итогового балла, ограничение от 30 до 100
        probability = min(100, max(30, score * 15))

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

    # Фильтруем по минимальной вероятности, если есть такие, иначе топ N по вероятности
    filtered = [coin for coin in scored_coins if coin['probability'] >= min_probability]
    if filtered:
        return sorted(filtered, key=lambda x: x['probability'], reverse=True)[:top_n]
    else:
        return sorted(scored_coins, key=lambda x: x['probability'], reverse=True)[:top_n]
