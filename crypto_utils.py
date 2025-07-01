from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

def get_top_ton_wallet_coins():
    # Примерный список популярных монет, доступных в Telegram Wallet
    coin_ids = [
        "bitcoin", "ethereum", "toncoin", "tether", "binancecoin", "usd-coin",
        "polygon", "litecoin", "tron", "solana", "dogecoin", "avalanche-2"
    ]

    coins = cg.get_price(
        ids=coin_ids,
        vs_currencies='usd',
        include_24hr_change=True
    )

    # Выбираем монету с максимальным ростом
    best = None
    max_change = -999

    for coin_id, data in coins.items():
        change = data.get('usd_24h_change', 0)
        if change > max_change:
            max_change = change
            best = {
                'id': coin_id,
                'price': data['usd'],
                'change': round(change, 2)
            }

    return best
