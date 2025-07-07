# Production-конфигурация
TELEGRAM_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
OWNER_ID = 347552741
DB_ACTIVE = True  # Флаг активности базы данных

def get_config():
    return {
        'token': TELEGRAM_TOKEN,
        'owner': OWNER_ID,
        'version': '2.1.0',
        'mode': 'production'
    }
