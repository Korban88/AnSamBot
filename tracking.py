import asyncio
import time
from collections import defaultdict
from crypto_utils import get_current_price
from config import OWNER_ID

# Структура: user_id -> list of dicts with coin_id, start_price, start_time
active_trackings = defaultdict(list)

CHECK_INTERVAL = 600  # 10 минут
TIMEOUT = 12 * 3600  # 12 часов

bot = None  # будет установлен извне через set_bot_instance()


def set_bot_instance(bot_instance):
    global bot
    bot = bot_instance


def start_tracking_coin(coin_id, user_id, start_price):
    active_trackings[user_id].append({
        "coin_id": coin_id,
        "start_price": start_price,
        "start_time": time.time()
    })


def stop_all_tracking(user_id):
    active_trackings[user_id] = []


async def tracking_loop():
    while True:
        for user_id, coins in list(active_trackings.items()):
            updated_coins = []
            for coin in coins:
                coin_id = coin["coin_id"]
                start_price = coin["start_price"]
                start_time = coin["start_time"]
                current_price = get_current_price(coin_id)

                if current_price is None:
                    updated_coins.append(coin)
                    continue

                change_pct = ((current_price - start_price) / start_price) * 100

                if change_pct >= 5:
                    await bot.send_message(user_id,
                        f"🚀 Монета *{coin_id}* выросла на +5%!\n"
                        f"Текущая цена: *{current_price:.4f}* USD",
                        parse_mode="Markdown")
                    continue

                elif change_pct >= 3.5:
                    await bot.send_message(user_id,
                        f"🔔 Монета *{coin_id}* приближается к цели:\n"
                        f"Рост уже составил *{change_pct:.2f}%*",
                        parse_mode="Markdown")

                elif time.time() - start_time > TIMEOUT:
                    await bot.send_message(user_id,
                        f"⏱ Монета *{coin_id}* отслеживалась 12 часов.\n"
                        f"Изменение цены: *{change_pct:.2f}%*\n"
                        f"Текущая цена: *{current_price:.4f}* USD",
                        parse_mode="Markdown")
                    continue

                updated_coins.append(coin)

            active_trackings[user_id] = updated_coins

        await asyncio.sleep(CHECK_INTERVAL)
