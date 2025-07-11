# cron_updater.py

import time
from crypto_utils import fetch_and_cache_indicators

if __name__ == "__main__":
    while True:
        print("✅ Обновление indicators_cache.json запущено...")
        fetch_and_cache_indicators()
        print("✅ Ожидание 30 минут до следующего обновления...")
        time.sleep(1800)  # 30 минут
