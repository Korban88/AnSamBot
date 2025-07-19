import asyncio
import time
from telegram import Bot

tracked_coins = {}

CHECK_INTERVAL = 600  # 10 минут
TARGET_INCREASE_1 = 3.5  # %
TARGET_INCREASE_2 = 5.0  # %
TIMEOUT_HOURS = 12


async def get_price(coin_id):
    from crypto_utils import get_current_prices
    prices = await get_current_prices([coin_id])
    return prices.get(coin_id, {}).get("usd")


async def track_coin_price(coin_id, chat_id, bot: Bot):
    start_price = await get_price(coin_id)
    if not start_price:
        await bot.send_message(chat_id, f"Не удалось получить цену {coin_id}")
        return

    start_time = time.time()
    tracked_coins[coin_id] = True

    while tracked_coins.get(coin_id, False):
        current_price = await get_price(coin_id)
        if not current_price:
            await asyncio.sleep(CHECK_INTERVAL)
            continue

        change_percent = ((current_price - start_price) / start_price) * 100

        if change_percent >= TARGET_INCREASE_2:
            await bot.send_message(chat_id, f"📈 {coin_id.upper()} вырос на +{TARGET_INCREASE_2}%!")
            tracked_coins.pop(coin_id, None)
            break
        elif change_percent >= TARGET_INCREASE_1:
            await bot.send_message(chat_id, f"🔔 {coin_id.upper()} достиг +{TARGET_INCREASE_1}% роста.")
        elif time.time() - start_time > TIMEOUT_HOURS * 3600:
            await bot.send_message(
                chat_id,
                f"⏱ Отслеживание {coin_id.upper()} завершено. За 12ч изменение составило {round(change_percent, 2)}%"
            )
            tracked_coins.pop(coin_id, None)
            break

        await asyncio.sleep(CHECK_INTERVAL)


def start_tracking(coin_id, chat_id):
    from telegram import Bot
    from config import TOKEN
    bot = Bot(token=TOKEN)
    asyncio.create_task(track_coin_price(coin_id, chat_id, bot))


def stop_all_trackings():
    tracked_coins.clear()
