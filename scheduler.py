# scheduler.py

import asyncio
from aiogram import Dispatcher, Bot
from datetime import datetime, timedelta, timezone
from crypto_utils import get_top_coins

MOSCOW_TZ = timezone(timedelta(hours=3))  # UTC+3

async def send_daily_signal(bot: Bot, user_id: int, get_top_coins_func):
    coins = get_top_coins_func()
    if not coins:
        await bot.send_message(user_id, "Не удалось получить сигналы.")
        return

    coin = coins[0]
    name = coin['id']
    price = coin['price']
    change = coin['change_24h']
    probability = coin['probability']
    target_price = coin['target_price']
    stop_loss_price = coin['stop_loss_price']

    text = (
        f"💰 *Ежедневный сигнал:*\n"
        f"Монета: {name}\n"
        f"Цена: *{price} $*\n"
        f"Рост за 24ч: {change}%\n"
        f"{'🟢' if probability >= 70 else '🔴'} Вероятность роста: {probability}%\n"
        f"🎯 Цель: *{target_price} $* \\(+5%\\)\n"
        f"⛔️ Стоп-лосс: {stop_loss_price} $ \\(-3\\.5%\\)"
    )

    await bot.send_message(user_id, text)

def schedule_daily_signal(dp: Dispatcher, bot: Bot, get_top_coins_func, user_id: int = None):
    async def daily_task():
        while True:
            now = datetime.now(MOSCOW_TZ)
            next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
            if next_run < now:
                next_run += timedelta(days=1)

            wait_seconds = (next_run - now).total_seconds()
            print(f"⏳ До следующего сигнала: {round(wait_seconds / 60, 1)} минут")
            await asyncio.sleep(wait_seconds)

            if user_id:
                await send_daily_signal(bot, user_id, get_top_coins_func)

    async def keep_awake():
        while True:
            try:
                await bot.get_me()  # "ping"
                print("🔁 Ping bot.get_me() — Railway не уснёт")
            except Exception as e:
                print(f"Ping error: {e}")
            await asyncio.sleep(900)  # каждые 15 минут

    asyncio.create_task(daily_task())
    asyncio.create_task(keep_awake())
