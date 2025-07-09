# config.py

TELEGRAM_BOT_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'  # токен твоего бота
OWNER_ID = 347552741  # твой Telegram ID

# Настройки сигнала (ослаблены для теста)
TARGET_PROFIT_PERCENT = 5.0
TRACKING_ALERT_PERCENT = 3.5
MAX_PRICE_DROP_24H = -7.0           # раньше было -3.0
MIN_GROWTH_PROBABILITY = 50.0       # раньше было 65.0

# Путь к кешу
INDICATORS_CACHE_FILE = "indicators_cache.json"
TOP3_CACHE_FILE = "top3_cache.json"
