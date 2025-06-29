import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import send_crypto_signal  # Убедись, что эта функция импортируется корректно
import logging

logging.basicConfig(level=logging.INFO)

async def job():
    try:
        logging.info("📡 Scheduled task started.")
        await send_crypto_signal()
        logging.info("✅ Signal sent successfully.")
    except Exception as e:
        logging.error(f"❌ Error in scheduled job: {e}")

async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(job, "cron", hour=8, minute=0)
    scheduler.start()
    
    logging.info("📅 Scheduler started. Waiting for 8:00 MSK...")
    
    # Keep the process alive
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
