from analysis import analyze_coin
from crypto_utils import get_top_coins

MIN_PROBABILITY = 65
MAX_DROP_24H = -3.0

def generate_signal():
    coins = get_top_coins()
    analyzed = []

    for coin in coins:
        try:
            metrics = analyze_coin(coin['id'])
            if not metrics:
                continue

            change_24h = coin['price_change_percentage_24h']
            probability = metrics['probability']

            if probability >= MIN_PROBABILITY and change_24h > MAX_DROP_24H:
                analyzed.append({
                    'id': coin['id'],
                    'symbol': coin['symbol'],
                    'name': coin['name'],
                    'price': coin['current_price'],
                    'change_24h': change_24h,
                    'probability': probability,
                    'rsi': metrics['rsi'],
                    'ma7': metrics['ma7'],
                    'ma20': metrics['ma20'],
                    'score': metrics['score']
                })
        except Exception as e:
            continue

    if not analyzed:
        return None

    analyzed.sort(key=lambda x: (x['probability'], x['score'], x['change_24h']), reverse=True)
    best = analyzed[0]

    return {
        'name': best['name'],
        'symbol': best['symbol'],
        'price': best['price'],
        'change_24h': best['change_24h'],
        'probability': best['probability'],
        'rsi': best['rsi'],
        'ma7': best['ma7'],
        'ma20': best['ma20'],
        'score': best['score'],
        'entry': round(best['price'], 4),
        'target': round(best['price'] * 1.05, 4),
        'stop': round(best['price'] * 0.965, 4)
    }
