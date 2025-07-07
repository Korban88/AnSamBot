from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.signal_generator import generate_top_signals
from aiogram import Bot
import os

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    async def send_daily_signal():
        signal = await generate_top_signals()
        await bot.send_message(
            os.getenv("OWNER_ID"),
            signal['top_1'],
            parse_mode="Markdown"
        )
    
    scheduler.add_job(
        send_daily_signal,
        'cron',
        hour=8,
        minute=0
    )
    scheduler.start()
