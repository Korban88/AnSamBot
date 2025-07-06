# tracking.py

import asyncio
import time
from datetime import datetime
from aiogram import Bot
from config import TELEGRAM_USER_ID
from crypto_utils import get_current_price

# Хранилище активных отслеживаний
active_trackings = {}

# Настройки отслеживания
CHECK_INTERVAL = 600  # каждые 10 минут
PRICE_TARGET_1 = 1.035
PRICE_TARGET_2 = 1.05
MAX_TRACKING_DURATION = 12 * 60 * 60  # 12 часов в секундах

async def track_price(bot: Bot, coin_id: str, entry_price: float):
    start_time = time.time()
    notified_3_5 = False
    notified_5 = False

    while True:
        current_price = await get_current_price(coin_id)

        if current_price is None:
            await bot.send_message(TELEGRAM_USER_ID, f"⚠️ Не удалось получить цену для {coin_id}. Отслеживание остановлено.")
            break

        price_change = current_price / entry_price
        elapsed = time.time() - start_time

        # Уведомление при +3.5%
        if price_change >= PRICE_TARGET_1 and not notified_3_5:
            await bot.send_message(
                TELEGRAM_USER_ID,
                f"📈 {coin_id.upper()} вырос на +3.5% от цены входа {entry_price:.4f} и сейчас стоит {current_price:.4f}."
            )
            notified_3_5 = True

        # Уведомление при +5%
        if price_change >= PRICE_TARGET_2 and not notified_5:
            await bot.send_message(
                TELEGRAM_USER_ID,
                f"🚀 {coin_id.upper()} достиг цели +5%!\nВход был: {entry_price:.4f}, сейчас: {current_price:.4f}"
            )
            notified_5 = True
            break

        # Отчёт по истечении 12 часов
        if elapsed >= MAX_TRACKING_DURATION:
            percent_change = ((current_price - entry_price) / entry_price) * 100
            await bot.send_message(
                TELEGRAM_USER_ID,
                f"⏱ Прошло 12 часов с начала отслеживания {coin_id.upper()}.\n"
                f"Цена была: {entry_price:.4f}, сейчас: {current_price:.4f}\n"
                f"Изменение: {percent_change:.2f}%"
            )
            break

        await asyncio.sleep(CHECK_INTERVAL)

    # Удаляем отслеживание
    if coin_id in active_trackings:
        del active_trackings[coin_id]

def start_tracking(bot: Bot, coin_id: str, entry_price: float):
    if coin_id not in active_trackings:
        task = asyncio.create_task(track_price(bot, coin_id, entry_price))
        active_trackings[coin_id] = task

def stop_all_trackings():
    for task in active_trackings.values():
        task.cancel()
    active_trackings.clear()
