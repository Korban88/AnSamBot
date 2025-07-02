import asyncio
import logging
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI
from aiogram import Bot

cg = CoinGeckoAPI()

# Словарь для отслеживания монет
tracked_coins = {}

async def start_tracking(bot: Bot, user_id: int, coin_id: str, start_price: float):
    logging.info(f"Начинаем отслеживание {coin_id} для пользователя {user_id} по цене {start_price}")
    tracked_coins[coin_id] = {
        "user_id": user_id,
        "start_price": start_price,
        "start_time": datetime.utcnow()
    }

    notified_3_5 = False
    notified_5 = False

    while True:
        await asyncio.sleep(600)  # Проверяем каждые 10 минут
        try:
            data = cg.get_price(ids=coin_id, vs_currencies='usd')
            current_price = data[coin_id]['usd']
            change_percent = ((current_price - start_price) / start_price) * 100

            if change_percent >= 5 and not notified_5:
                await bot.send_message(user_id,
                    f"🚀 Монета {coin_id} выросла на 5% с момента начала отслеживания!\nЦена была: {start_price}, стала: {current_price:.4f} (+{change_percent:.2f}%)")
                notified_5 = True
                tracked_coins.pop(coin_id, None)
                break

            elif change_percent >= 3.5 and not notified_3_5:
                await bot.send_message(user_id,
                    f"📈 Монета {coin_id} выросла на 3.5%!\nЦена была: {start_price}, стала: {current_price:.4f} (+{change_percent:.2f}%)")
                notified_3_5 = True

            # Проверка на 12 часов
            if datetime.utcnow() - tracked_coins[coin_id]['start_time'] > timedelta(hours=12):
                trend = "выросла" if change_percent > 0 else "упала"
                await bot.send_message(user_id,
                    f"⏱ 12 часов прошло с момента отслеживания монеты {coin_id}.\nОна {trend} на {abs(change_percent):.2f}%.\nНачальная цена: {start_price}, текущая: {current_price:.4f}.")
                tracked_coins.pop(coin_id, None)
                break

        except Exception as e:
            logging.error(f"Ошибка при отслеживании {coin_id}: {e}")
            await bot.send_message(user_id, f"Ошибка при отслеживании монеты {coin_id}.")
            tracked_coins.pop(coin_id, None)
            break
