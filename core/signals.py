from core.analysis import analyze_coin
from core.api.coingecko import fetch_coin_data
from data.crypto_list import CRYPTO_LIST

async def generate_daily_signal():
    signals = []
    for coin in CRYPTO_LIST:
        data = await fetch_coin_data(coin['id'])
        if analyze_coin(data):
            signals.append({
                'coin': coin['symbol'],
                'price': data['price'],
                'rsi': data['rsi'],
                'target': data['price'] * 1.05,
                'stop_loss': data['price'] * 0.97
            })
    
    return sorted(signals, key=lambda x: x['rsi'])[0] if signals else None
