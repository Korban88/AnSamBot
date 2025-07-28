from apscheduler.schedulers.background import BackgroundScheduler
from analysis import analyze_cryptos
from utils import save_signal_cache
import logging
import asyncio

def schedule_signal_refresh():
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    loop = asyncio.get_event_loop()

    async def refresh_signal_cache():
        try:
            signals = await analyze_cryptos()
            save_signal_cache(signals)
            logging.info("♻️ Сигналы автоматически обновлены")
        except Exception as e:
            logging.error(f"Ошибка при автообновлении сигналов: {e}")

    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(refresh_signal_cache(), loop),
        "interval", hours=3
    )
    scheduler.start()
