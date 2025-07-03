from pycoingecko import CoinGeckoAPI
from ton_tokens import get_ton_wallet_tokens

cg = CoinGeckoAPI()

def get_top_ton_wallet_coins(top_n=1):
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

        # === Новый анализ и расчёт вероятности ===
        score = 0
        score += change_24h * 1.5                # рост за 24ч — вес 1.5
        score += (change_7d or 0) * 1.0          # рост за 7д — вес 1.0
        score += min(volume / 1_000_000, 10)     # вес от объёма (до 10)

        score = max(0, min(score, 100))          # ограничение 0–100
        probability = round(score)

        scored_coins.append({
            'id': name,
            'price': round(price, 4),
            'change_24h': round(change_24h, 2),
            'change_7d': round(change_7d, 2) if change_7d is not None else 0,
            'volume': int(volume),
            'probability': probability
        })

    scored_coins.sort(key=lambda x: x['probability'], reverse=True)
    return scored_coins[:top_n]
