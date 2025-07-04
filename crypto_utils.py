import requests
import logging
from ton_tokens import get_ton_wallet_tokens
from tech_analysis import analyze_coin

def get_top_coins():
    try:
        token_ids = get_ton_wallet_tokens()
        ids_str = ",".join(token_ids)
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ids_str,
            "order": "market_cap_desc",
            "per_page": len(token_ids),
            "page": 1,
            "price_change_percentage": "24h,7d"
        }
        response = requests.get(url, params=params)
        data = response.json()

        good_coins = []

        for coin in data:
            coin_id = coin["id"]
            price = coin.get("current_price")
            change_24h = coin.get("price_change_percentage_24h_in_currency", 0)
            volume = coin.get("total_volume", 0)

            # ❌ Отсеиваем по падению и объему
            if change_24h < -3 or volume < 10_000_000:
                continue

            ta = analyze_coin(coin_id)
            if not ta or ta['probability'] < 65:
                continue

            coin_info = {
                "id": coin_id,
                "price": price,
                "change_24h": round(change_24h, 2),
                "probability": ta['probability'],
                "ma7": ta['ma7'],
                "ma20": ta['ma20'],
                "rsi": ta['rsi'],
                "score": ta['score'],
                "target_price": round(price * 1.05, 4),
                "stop_loss_price": round(price * 0.965, 4),
            }

            logging.info(f"[Анализ] {coin_id}: prob={ta['probability']}%, vol={volume}, 24h={change_24h}%")
            good_coins.append(coin_info)

        sorted_coins = sorted(good_coins, key=lambda x: x["probability"], reverse=True)
        logging.info(f"✅ Монет отобрано: {len(sorted_coins)}")

        return sorted_coins[:3]

    except Exception as e:
        logging.error(f"Ошибка в get_top_coins: {e}")
        return []
