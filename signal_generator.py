from analysis import analyze_coin
from crypto_utils import get_top_coins

# Порог вероятности для выбора лучших монет
MIN_PROBABILITY = 65

def generate_signal(return_top3=False):
    coins = get_top_coins()
    analyzed = []

    for coin in coins:
        try:
            metrics = analyze_coin(coin['id'])
            if metrics and metrics['probability'] >= MIN_PROBABILITY and coin['price_change_percentage_24h'] > -3:
                analyzed.append({
                    'id': coin['id'],
                    'symbol': coin['symbol'],
                    'name': coin['name'],
                    'price': coin['current_price'],
                    'change_24h': coin['price_change_percentage_24h'],
                    'probability': metrics['probability'],
                    'rsi': metrics['rsi'],
                    'ma7': metrics['ma7'],
                    'ma20': metrics['ma20'],
                    'score': metrics['score']
                })
        except Exception:
            continue

    if not analyzed:
        return [] if return_top3 else None

    # Сортировка по вероятности и изменению цены
    analyzed.sort(key=lambda x: (x['probability'], x['change_24h']), reverse=True)

    if return_top3:
        return analyzed[:3]

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
