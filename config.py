import os

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c")
    OWNER_ID = 347552741
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "ваш_ключ")
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")  # Для будущей интеграции

config = Config()
