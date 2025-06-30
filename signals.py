import random

def get_crypto_signal():
    coins = ["TON", "BTC", "ETH", "USDT", "BNB", "SOL", "DOGE", "AVAX", "LTC"]
    coin = random.choice(coins)
    return {
        "coin": coin,
        "action": "BUY",
        "target_profit_percent": 5.0
    }
