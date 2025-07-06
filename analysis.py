import aiohttp
import asyncio
import json
import os
from datetime import datetime, timedelta

from crypto_utils import get_current_price, get_moving_average, get_rsi
from crypto_list import crypto_list

async def analyze_cryptos(coin_data):
    scores = []

    for coin in crypto_list:
        coin_id = coin["id"]
        symbol = coin["symbol"]

        data = coin_data.get(coin_id)
        if not data:
            continue

        try:
            price = data["current_price"]
            ma = await get_moving_average(coin_id)
            rsi = await get_rsi(coin_id)
            change_24h = data["price_change_percentage_24h"]

            score = 0

            if price > ma:
                score += 1
            if 40 <= rsi <= 65:
                score += 1
            if change_24h > 0:
                score += 1

            if change_24h < -3:
                continue

            probability = round((score / 3) * 100)

            if probability >= 65:
                scores.append({
                    "id": coin_id,
                    "symbol": symbol,
                    "score": score,
                    "probability": probability,
                    "price": price,
                    "ma": ma,
                    "rsi": rsi,
                    "change_24h": change_24h
                })

        except Exception:
            continue

    scores.sort(key=lambda x: x["probability"], reverse=True)

    return scores[:3]
