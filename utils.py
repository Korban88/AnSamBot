import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time, timedelta
from telegram import Bot
from analysis import get_top_signal
from config import OWNER_ID, TELEGRAM_BOT_TOKEN

used_symbols_file = "used_symbols.json"
indicators_cache_file = "indicators_cache.json"

def reset_cache():
    with open(used_symbols_file, "w") as f:
        json.dump([], f)
    with open(indicators_cache_file, "w") as f:
        json.dump({}, f)

# Планировщик ежедневного сигнала
def schedule_daily_signal_check(app):
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    async def job():
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        signal = await get_top_signal()
        if signal:
            message = (
                f"Ежедневный сигнал\n\n"
                f"Монета: *{signal['symbol']}*\n"
                f"Цена входа: *{signal['entry_price']}* $\n"
                f"Цель +5%: *{signal['target_price']}* $\n"
                f"Стоп-лосс: *{signal['stop_loss']}* $\n"
                f"Изменение за 24ч: *{signal['change_24h']}%*\n"
                f"Вероятность роста: *{signal['probability']}%*"
            )
            await bot.send_message(chat_id=OWNER_ID, text=message, parse_mode="Markdown")

    # Настроим запуск каждый день в 8:00
    scheduler.add_job(job, trigger="cron", hour=8, minute=0)
    scheduler.start()
