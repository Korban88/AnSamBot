from pycoingecko import CoinGeckoAPI
from ton_tokens import get_ton_wallet_tokens

cg = CoinGeckoAPI()

def analyze_tokens():
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
        try:
            price = coin.get('current_price')
            volume = coin.get('total_volume')
            change_24h = coin.get('price_change_percentage_24h_in_currency', 0)
            change_7d = coin.get('price_change_percentage_7d_in_currency', 0)
            name = coin.get('id')

            if price is None or volume is None:
                continue  # пропускаем, если данных нет

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
                    'score': score,
                    'probability': min(95, 60 + score * 5)  # доп поле: вероятность
                }
        except Exception as e:
            print(f"⚠️ Ошибка при обработке монеты: {e}")
            continue

    return best_coin
