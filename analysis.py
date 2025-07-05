import httpx
import logging
from typing import List, Dict
from crypto_list import crypto_list

logger = logging.getLogger(__name__)

async def analyze_cryptos() -> List[Dict[str, str]]:
    analyzed_data = []
    headers = {"accept": "application/json"}
    coin_ids = [coin["id"] for coin in crypto_list]

    # Разбиваем на батчи по 20, чтобы не вызывать ошибку 429
    batch_size = 20
    for i in range(0, len(coin_ids), batch_size):
        batch_ids = coin_ids[i:i + batch_size]
        ids_str = ",".join(batch_ids)
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids_str}&price_change_percentage=24h"

        try:
            response = await httpx.AsyncClient().get(url, headers=headers, timeout=15)
            response.raise_for_status()
            market_data = response.json()
        except Exception as e:
            logger.warning(f"Ошибка при получении батча данных: {e}")
            continue

        for coin in market_data:
            try:
                name = coin["id"].upper()
                price = coin.get("current_price")
                change_24h = coin.get("price_change_percentage_24h") or 0
                volume = coin.get("total_volume") or 0
                market_cap = coin.get("market_cap") or 0

                if price is None:
                    continue

                # Фильтры
                if any(sub in name.lower() for sub in ["dog", "cat", "meme", "pepe", "elon"]):
                    continue
                if price < 0.005 or volume < 100_000 or market_cap < 10_000_000:
                    continue
                if change_24h < -3:
                    continue

                # Улучшенный скоринг
                score = 0

                # Изменение цены — до 0.3
                if change_24h > 0:
                    score += min(change_24h / 10, 1) * 0.3

                # Объём торгов — до 0.2
                score += min(volume / 10_000_000, 1) * 0.2

                # Капитализация — до 0.2
                score += min(market_cap / 1_000_000_000, 1) * 0.2

                # Ликвидность — до 0.2
                liquidity_ratio = volume / market_cap if market_cap > 0 else 0
                score += min(liquidity_ratio, 1) * 0.2

                # Бонус за рост и оборот — до 0.1
                if change_24h > 3 and volume > 5_000_000:
                    score += 0.1

                probability = round(min(score, 0.99) * 100, 1)

                if probability < 65:
                    continue

                entry_price = round(price, 6)
                target_price = round(entry_price * 1.05, 6)
                stop_loss = round(entry_price * 0.97, 6)

                analyzed_data.append({
                    "name": name,
                    "growth_probability": probability,
                    "price": entry_price,
                    "target_price": target_price,
                    "stop_loss": stop_loss
                })
            except Exception as ex:
                logger.warning(f"Ошибка при анализе монеты {coin.get('id')}: {ex}")
                continue

    analyzed_data.sort(key=lambda x: x["growth_probability"], reverse=True)
    return analyzed_data[:10]
