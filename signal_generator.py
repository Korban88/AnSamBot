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

    # Сортировка по вероятности (и по 24h изменению как второму критерию)
    analyzed.sort(key=lambda x: (x['probability'], x['change_24h']), reverse=True)

    if return_top3:
        return [_prepare_signal_data(c) for c in analyzed[:3]]
    return _prepare_signal_data(analyzed[0])


def _prepare_signal_data(coin):
    return {
        'name': coin['name'],
        'symbol': coin['symbol'],
        'price': coin['price'],
        'change_24h': round(coin['change_24h'], 2),
        'probability': coin['probability'],
        'rsi': coin['rsi'],
        'ma7': coin['ma7'],
        'ma20': coin['ma20'],
        'score': coin['score'],
        'entry': round(coin['price'], 4),
        'target': round(coin['price'] * 1.05, 4),
        'stop': round(coin['price'] * 0.965, 4)
    }
