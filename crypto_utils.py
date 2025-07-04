import requests
from analysis import analyze_coin
from get_ton_wallet_tokens import get_ton_wallet_tokens
import logging

def get_current_data(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json().get(coin_id, {})
        return float(data.get('usd', 0)), float(data.get('usd_24h_change', 0))
    except Exception as e:
        logging.warning(f"[!] Ошибка получения данных {coin_id}: {e}")
        return 0, 0

def get_top_coins():
    result = []
    coins = get_ton_wallet_tokens()
    for coin_id in coins:
        try:
            analysis = analyze_coin(coin_id)
            if not analysis:
                continue

            price, change_24h = get_current_data(coin_id)
            if price == 0:
                continue

            probability = analysis["probability"]

            # Жёсткие фильтры
            if probability < 65 or change_24h < -3:
                continue

            coin_data = {
                'id': coin_id,
                'price': round(price, 4),
                'change_24h': round(change_24h, 2),
                'probability': probability,
                'target_price': round(price * 1.05, 4),
                'stop_loss_price': round(price * 0.965, 4)
            }

            logging.info(f"[Анализ] {coin_id}: prob={probability}%, vol={analysis['volume_last']}, 24h={change_24h}%")
            result.append(coin_data)

        except Exception as e:
            logging.warning(f"⚠️ Ошибка при анализе {coin_id}: {e}")

    logging.info(f"✅ Монет отобрано: {len(result)}")
    return sorted(result, key=lambda x: x['probability'], reverse=True)[:3]
