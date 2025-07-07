# Production Config (v2.1.2)
TELEGRAM_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
OWNER_ID = 347552741
DB_ACTIVE = True

def get_config():
    return {
        'version': '2.1.2',
        'mode': 'production',
        'token': TELEGRAM_TOKEN,  # Добавлено это поле
        'owner': OWNER_ID,
        'db_status': DB_ACTIVE
    }
