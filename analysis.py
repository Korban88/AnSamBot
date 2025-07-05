import httpx
import logging
from crypto_list import crypto_list
from crypto_utils import get_rsi, get_moving_average

logger = logging.getLogger(__name__)

def analyze_cryptos():
    crypto_ids = [crypto["id"] for crypto in crypto_list]
    all_data = []
    batch_size = 20

    for i in range(0, len(crypto_ids), batch_size):
        batch_ids = crypto_ids[i:i+batch_size]
        url = f"https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ",".join(batch_ids),
            "price_change_percentage": "24h"
        }

        try:
            response = httpx.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Получено монет в партии: {len(data)}")
            all_data.extend(data)
        except httpx.HTTPError as e:
            logger.error(f"❌ Ошибка запроса CoinGecko: {e}")
            continue

    logger.info(f"📊 Всего монет получено: {len(all_data)}")

    analyzed = []

    for coin in all_data:
        try:
            rsi = get_rsi(coin["id"])
            ma = get_moving_average(coin["id"])
            price_change_24h = coin.get("price_change_percentage_24h_in_currency", 0.0)
            current_price = coin["current_price"]

            if ma is None or rsi is None:
                logger.warning(f"⚠️ Пропуск монеты {coin['id']} из-за отсутствия RSI или MA")
                continue

            trend_score = 0
            explanation = []

            if price_change_24h > 0:
                trend_score += price_change_24h / 2
                explanation.append(f"Рост за 24ч: {price_change_24h:.2f}%")

            if 45 < rsi < 70:
                trend_score += 10
                explanation.append(f"RSI: {rsi:.1f} (нормальный)")

            if current_price > ma:
                trend_score += 7
                explanation.append(f"Цена выше MA ({ma:.2f})")
            else:
                explanation.append(f"Цена ниже MA ({ma:.2f})")

            probability = min(round(50 + trend_score, 2), 95)

            if probability >= 65 and price_change_24h > -3:
                analyzed.append({
                    "id": coin["id"],
                    "symbol": coin["symbol"],
                    "name": coin["name"],
                    "price": current_price,
                    "price_change_24h": price_change_24h,
                    "rsi": rsi,
                    "ma": ma,
                    "probability": probability,
                    "explanation": explanation
                })

        except Exception as e:
            logger.error(f"⚠️ Ошибка при анализе {coin['id']}: {e}")

    logger.info(f"🎯 Монет после фильтрации: {len(analyzed)}")

    top_3 = sorted(analyzed, key=lambda x: x["probability"], reverse=True)[:3]
    logger.info(f"🏆 Отобрано top-3 монет: {[x['symbol'] for x in top_3]}")

    return top_3
