from apscheduler.schedulers.background import BackgroundScheduler
from analysis import analyze_cryptos
from utils import save_signal_cache
import logging

def schedule_signal_refresh():
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")

    async def refresh_signal_cache():
        try:
            signals = await analyze_cryptos()
            save_signal_cache(signals)
            logging.info("♻️ Сигналы автоматически обновлены")
        except Exception as e:
            logging.error(f"Ошибка при автообновлении сигналов: {e}")

    from asyncio import create_task
    scheduler.add_job(lambda: create_task(refresh_signal_cache()), "interval", hours=3)
    scheduler.start()
