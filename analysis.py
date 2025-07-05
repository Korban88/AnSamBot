import logging
import httpx
from crypto_list import crypto_list

logger = logging.getLogger(__name__)

async def analyze_cryptos():
    try:
        # Извлекаем только id монет
        coin_ids = [coin["id"] for coin in crypto_list]

        # Разбиваем на чанки по 20 (ограничение Coingecko)
        chunk_size = 20
        coin_chunks = [coin_ids[i:i + chunk_size] for i in range(0, len(coin_ids), chunk_size)]

        all_data = []

        for chunk in coin_chunks:
            ids_param = ",".join(chunk)
            url = (
                "https://api.coingecko.com/api/v3/coins/markets"
                f"?vs_currency=usd&ids={ids_param}&price_change_percentage=24h"
            )

            response = httpx.get(url)
            if response.status_code == 429:
                logger.warning("Analysis: Ошибка при получении данных: 429 Too Many Requests")
                break

            data = response.json()
            all_data.extend(data)

        # Фильтруем: исключаем монеты с падением более 3%
        filtered = [
            coin for coin in all_data
            if coin.get("price_change_percentage_24h") is not None and coin["price_change_percentage_24h"] > -3
        ]

        # Оцениваем и сортируем
        scored = []
        for coin in filtered:
            price = coin["current_price"]
            score = 0

            # Чем выше рост за 24ч — тем лучше
            price_change_24h = coin["price_change_percentage_24h"] or 0
            score += price_change_24h

            # Дополнительно можно учитывать объем, market cap, волатильность и т.п.

            probability = min(95, max(50, round(score)))  # от 50 до 95%

            target_price = round(price * 1.05, 6)
            stop_loss = round(price * 0.97, 6)

            scored.append({
                "name": coin["id"],
                "price": price,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "growth_probability": probability,
            })

        # Оставляем только монеты с вероятностью роста от 65%
        top_coins = sorted(
            [coin for coin in scored if coin["growth_probability"] >= 65],
            key=lambda x: x["growth_probability"],
            reverse=True
        )

        return top_coins[:3]

    except Exception as e:
        logger.error(f"❌ Ошибка при анализе монет: {e}")
        return []
