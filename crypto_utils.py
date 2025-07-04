import requests
import logging
from ton_tokens import get_ton_wallet_tokens

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

            # 🔍 Простая аналитика
            score = 0
            score += 1 if change_24h > 0 else 0
            score += 1 if change_7d > 0 else 0
            score += 1 if volume > 10_000_000 else 0
            score += 1 if change_24h > 3 else 0
            score += 1 if change_7d > 5 else 0

            # 🔢 Примерно рассчитываем вероятность
            probability = min(95, max(30, score * 10 + int(change_24h)))

            # 🟠 Пометка монеты как рискованной (если просела более чем на 3% за 24ч)
            risky = change_24h < -3

            target_price = round(price * 1.05, 4)
            stop_loss_price = round(price * 0.965, 4)

            coin_info = {
                "id": coin.get("id"),
                "price": price,
                "change_24h": round(change_24h, 2),
                "change_7d": round(change_7d, 2),
                "volume": volume,
                "score": score,
                "probability": probability,
                "target_price": target_price,
                "stop_loss_price": stop_loss_price,
                "risky": risky
            }

            logging.info(f"Анализ монеты {coin_info['id']}: score={score}, prob={probability}, risky={risky}")
            good_coins.append(coin_info)

        # Сортировка по вероятности и объёму
        sorted_coins = sorted(good_coins, key=lambda x: (x['probability'], x['volume']), reverse=True)

        logging.info(f"Отобрано монет: {len(sorted_coins)}")
        return sorted_coins[:10]

    except Exception as e:
        logging.error(f"Ошибка в get_top_coins: {e}")
        return []
