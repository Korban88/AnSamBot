import httpx
import logging
from statistics import mean

logger = logging.getLogger(__name__)

COINS = [
    "storj", "uma", "anime", "ssv-network", "civic", "biconomy", "iost", "wax",
    "yield-guild-games", "bio", "immutable-x", "the-graph", "jito-governance-token",
    "curve-dao-token", "floki", "ethereum-name-service", "theta-token", "lido-dao",
    "jasmycoin", "miota", "bittorrent", "aptos", "near", "internet-computer",
    "ethereum-classic", "ondo-finance", "kaspa", "proof-of-liquidity", "mantle",
    "maga", "arbitrum", "render-token", "deepbrain-chain", "morpho-network",
    "starknet", "compound-governance-token", "dydx", "reserve-rights-token",
    "conflux-token", "neo", "multiversx", "mog-coin", "axie-infinity",
    "sats-ordinals", "pha", "everipedia", "memecoin", "aevo", "lisk", "dogs-token",
    "balancer", "illuvium", "scroll", "tensor"
]

BATCH_SIZE = 20

async def fetch_market_data(session, batch):
    ids = ",".join(batch)
    url = f"https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ids,
        "price_change_percentage": "24h"
    }
    try:
        response = await session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.warning(f"Ошибка при получении батча данных: {e}")
        return []

def calculate_score(coin):
    score = 0

    # 1. Рост за 24ч
    change_24h = coin.get("price_change_percentage_24h", 0)
    if change_24h > 5:
        score += 2
    elif change_24h > 2:
        score += 1
    elif change_24h < -2:
        score -= 1

    # 2. Объём торгов
    volume = coin.get("total_volume", 0)
    market_cap = coin.get("market_cap", 1)
    volume_ratio = volume / market_cap if market_cap else 0
    if volume_ratio > 0.15:
        score += 2
    elif volume_ratio > 0.07:
        score += 1

    # 3. Устойчивость: цена выше средней
    current_price = coin.get("current_price", 0)
    high_24h = coin.get("high_24h", 0)
    low_24h = coin.get("low_24h", 0)
    avg_price = mean([high_24h, low_24h]) if high_24h and low_24h else current_price
    if current_price > avg_price:
        score += 1

    return score

def score_to_probability(score):
    if score >= 5:
        return 80
    elif score == 4:
        return 70
    elif score == 3:
        return 65
    elif score == 2:
        return 60
    else:
        return 50

async def analyze_cryptos():
    top_coins = []
    async with httpx.AsyncClient(timeout=15) as session:
        for i in range(0, len(COINS), BATCH_SIZE):
            batch = COINS[i:i + BATCH_SIZE]
            data = await fetch_market_data(session, batch)
            for coin in data:
                score = calculate_score(coin)
                probability = score_to_probability(score)
                if probability >= 60:
                    top_coins.append({
                        "name": coin["id"],
                        "price": coin["current_price"],
                        "target_price": round(coin["current_price"] * 1.05, 4),
                        "stop_loss": round(coin["current_price"] * 0.97, 4),
                        "growth_probability": probability
                    })

    sorted_coins = sorted(top_coins, key=lambda x: x["growth_probability"], reverse=True)
    return sorted_coins[:3]
