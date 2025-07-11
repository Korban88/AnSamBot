# cron_updater.py
import asyncio
import logging
import time
from crypto_utils import fetch_and_cache_indicators

logging.basicConfig(level=logging.INFO)

async def cron_updater():
    while True:
        logging.info("Запуск фонового обновления индикаторов...")
        fetch_and_cache_indicators()
        logging.info("Ожидание до следующего обновления...")
        await asyncio.sleep(1800)  # 30 минут

if __name__ == "__main__":
    try:
        asyncio.run(cron_updater())
    except KeyboardInterrupt:
        print("Остановлено пользователем")
