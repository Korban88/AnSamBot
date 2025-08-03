from apscheduler.schedulers.background import BackgroundScheduler
from analysis import analyze_cryptos
from utils import save_signal_cache
from tracking import CoinTracker
import logging
import asyncio

def schedule_signal_refresh(app):
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    loop = asyncio.get_event_loop()

    async def refresh_signal_cache():
        try:
            signals = await analyze_cryptos()
            save_signal_cache(signals)
            logging.info("♻️ Сигналы автоматически обновлены")
        except Exception as e:
            logging.error(f"Ошибка при автообновлении сигналов: {e}")

    async def send_evening_report():
        try:
            from telegram.ext import ContextTypes
            class DummyContext:
                bot = app.bot
            dummy_context = DummyContext()
            await CoinTracker.evening_report(dummy_context)
        except Exception as e:
            logging.error(f"Ошибка при отправке вечернего отчёта: {e}")

    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(refresh_signal_cache(), loop),
        "interval", hours=3
    )

    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(send_evening_report(), loop),
        "cron", hour=20, minute=0
    )

    scheduler.start()
