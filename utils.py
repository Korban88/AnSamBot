import random

def get_daily_crypto_signal():
    # Пример данных — в будущем можно подключить реальную аналитику
    coins = ["TON", "BTC", "ETH", "USDT", "BNB"]
    coin = random.choice(coins)
    signal = {
        "coin": coin,
        "action": "BUY",
        "target_profit_percent": 5.0
    }
    return signal
