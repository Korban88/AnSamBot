from core.api.coingecko import fetch_coin_data

def analyze_coin(coin_data):
    conditions = [
        coin_data['rsi'] < 45,
        coin_data['ma50'] > coin_data['ma200'],
        -6 <= coin_data['24h_change'] <= 0,
        coin_data['volume_change_24h'] > 10
    ]
    return all(conditions)
