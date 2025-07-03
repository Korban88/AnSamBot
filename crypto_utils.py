from pycoingecko import CoinGeckoAPI
from ton_tokens import get_ton_wallet_tokens

cg = CoinGeckoAPI()

def get_top_coins(top_n: int = 3, min_probability: int = 70):
    try:
        coin_ids = get_ton_wallet_tokens()
        if not coin_ids:
            print("⚠️ get_ton_wallet_tokens() вернул пусто.")
            return []

        coins = cg.get_coins_markets(
            vs_currency='usd',
            ids=coin_ids,
            order='market_cap_desc',
            per_page=250,
            price_change_percentage='24h,7d'
        )

        if not coins:
            print("⚠️ CoinGecko не вернул данных по монетам.")
            return []

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

            probability = min(100, max(30, score * 10))

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

        if not scored_coins:
            print("⚠️ Ни одна монета не прошла предварительную фильтрацию.")
            return []

        # монеты, у которых вероятность >= min_probability
        filtered = [coin for coin in scored_coins if coin['probability'] >= min_probability]

        # если filtered пустой — всё равно возвращаем top_n лучших
        if not filtered:
            print("ℹ️ Нет монет с probability >= min_probability. Возвращаю top_n по убыванию вероятности.")
            return sorted(scored_coins, key=lambda x: x['probability'], reverse=True)[:top_n]

        return sorted(filtered, key=lambda x: x['probability'], reverse=True)[:top_n]

    except Exception as e:
        print(f"❌ Ошибка в get_top_coins(): {e}")
        return []
