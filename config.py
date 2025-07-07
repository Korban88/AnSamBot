import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c")
OWNER_ID = os.getenv("OWNER_ID", "347552741")

# Тихая проверка переменных
if not os.getenv("TELEGRAM_TOKEN") or not os.getenv("OWNER_ID"):
    pass  # Не выводим ошибку, если есть fallback
