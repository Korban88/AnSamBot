import asyncio
from aiogram import Dispatcher, Bot
from datetime import datetime, timedelta, timezone
from crypto_utils import get_top_coins

MOSCOW_TZ = timezone(timedelta(hours=3))  # UTC+3

def esc(text):
    return str(text).replace("-", "\\-").replace(".", "\\.").replace("(", "\\(").replace(")", "\\)").replace("+", "\\+").replace("%", "\\%").replace("$", "\\$").replace("_", "\\_")

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
    ma7 = coin["analysis"].get("ma7")
    ma20 = coin["analysis"].get("ma20")
    rsi_val = coin["analysis"].get("rsi")

    text = (
        f"💰 *Ежедневный сигнал:*\n"
        f"Монета: *{esc(name)}*\n"
        f"Цена: *{esc(price)} \\$*\n"
        f"Рост за 24ч: *{esc(change)}\\%*\n"
        f"RSI: *{esc(rsi_val)}*\n"
        f"MA7: *{esc(ma7)}*, MA20: *{esc(ma20)}*\n"
        f"{'🟢' if probability >= 70 else '🔴'} Вероятность роста: *{esc(probability)}\\%*\n"
        f"🎯 Цель: *{esc(target_price)} \\$* \\(\\+5\\%\\)\n"
        f"⛔️ Стоп\\-лосс: *{esc(stop_loss_price)} \\$* \\(\\-3\\.5\\%\\)"
    )

    await bot.send_message(user_id, text, parse_mode="MarkdownV2")

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
                await bot.get_me()
                print("🔁 Ping bot.get_me() — Railway не уснёт")
            except Exception as e:
                print(f"Ping error: {e}")
            await asyncio.sleep(900)

    asyncio.create_task(daily_task())
    asyncio.create_task(keep_awake())
