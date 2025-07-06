from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.signal_generator import generate_daily_signal
from aiogram import Bot

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    @scheduler.scheduled_job("cron", hour=8, minute=0)
    async def send_daily_signal():
        signal = await generate_daily_signal()
        await bot.send_message(
            os.getenv("OWNER_ID"),
            signal["top_1"],
            parse_mode="MarkdownV2"
        )
    
    scheduler.start()
