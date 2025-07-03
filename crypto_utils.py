from ton_tokens import get_ton_wallet_tokens

def get_top_coins(top_n: int = 3, min_probability: int = 0):
    coin_ids = get_ton_wallet_tokens()
    if not coin_ids:
        print("Пустой список монет!")
        return []

    result = []
    for i, coin_id in enumerate(coin_ids[:top_n]):
        price = 1.23 + i
        change_24h = 5 + i
        change_7d = 10 + i
        volume = 1_000_000 + i * 1000
        probability = 80
        target_price = round(price * 1.05, 4)
        stop_loss_price = round(price * 0.965, 4)

        result.append({
            'id': coin_id,
            'price': price,
            'change_24h': change_24h,
            'change_7d': change_7d,
            'volume': volume,
            'probability': probability,
            'target_price': target_price,
            'stop_loss_price': stop_loss_price
        })

    print(f"Тестовый список монет: {result}")
    return result
