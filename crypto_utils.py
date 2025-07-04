import requests
import logging
from ton_tokens import get_ton_wallet_tokens
from analysis import analyze_coin

def get_top_coins():
    try:
        token_ids = get_ton_wallet_tokens()
        ids_str = ",".join(token_ids)
        url = f"https://api.coingecko.com/api/v3/coins/markets"
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
            price = coin.get("current_price")
            change_24h = coin.get("price_change_percentage_24h_in_currency", 0)
            change_7d = coin.get("price_change_percentage_7d_in_currency", 0)
            volume = coin.get("total_volume", 0)
            coin_id = coin.get("id")

            # ❌ Фильтр на падение за 24ч
            if change_24h < -3:
                continue

            # 📊 Анализ по RSI, MA
            analysis_data = analyze_coin(coin_id)
            if not analysis_data:
                continue

            probability = analysis_data['probability']
            if probability < 65:
                continue

            target_price = round(price * 1.05, 4)
            stop_loss_price = round(price * 0.965, 4)

            coin_info = {
                "id": coin_id,
                "price": price,
                "change_24h": round(change_24h, 2),
                "change_7d": round(change_7d, 2),
                "volume": volume,
                "probability": probability,
                "target_price": target_price,
                "stop_loss_price": stop_loss_price,
                "risky": change_24h < -3,
                "analysis": analysis_data
            }

            logging.info(f"[Анализ] {coin_id}: prob={probability}%, vol={volume}, 24h={change_24h}%")
            good_coins.append(coin_info)

        # Сортировка: по вероятности + объёму
        sorted_coins = sorted(good_coins, key=lambda x: (x['probability'], x['volume']), reverse=True)

        logging.info(f"✅ Монет отобрано: {len(sorted_coins)}")
        return sorted_coins[:10]

    except Exception as e:
        logging.error(f"❌ Ошибка в get_top_coins: {e}")
        return []
