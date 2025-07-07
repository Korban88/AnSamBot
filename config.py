import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c")
OWNER_ID = os.getenv("OWNER_ID", "347552741")

if not TELEGRAM_TOKEN or not OWNER_ID:
    print("⚠️ Внимание: Используются fallback-значения переменных!")
