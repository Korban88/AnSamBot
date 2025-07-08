# tracking.py

import asyncio
import time
from config import OWNER_ID
from crypto_utils import get_current_price
from telegram import Bot

# {coin_id: {"start_price": ..., "start_time": ...}}
active_trackings = {}

async def track_price(bot: Bot, coin_id: str):
    if coin_id in active_trackings:
        return  # Уже отслеживается

    start_price = get_current_price(coin_id)
    if not start_price:
        return

    active_trackings[coin_id] = {
        "start_price": start_price,
        "start_time": time.time()
    }

    notified_3_5 = False
    notified_5 = False
    notified_timeout = False

    while True:
        await asyncio.sleep(600)  # каждые 10 минут

        current_price = get_current_price(coin_id)
        if not current_price:
            continue

        start_data = active_trackings[coin_id]
        start_price = start_data["start_price"]
        change_percent = ((current_price - start_price) / start_price) * 100

        # Уведомление при +3.5%
        if change_percent >= 3.5 and not notified_3_5:
            await bot.send_message(
                chat_id=OWNER_ID,
                text=f"📈 Монета *{coin_id}* выросла на +3.5% с начала отслеживания!\n\nТекущая цена: ${current_price:.4f}",
                parse_mode="Markdown"
            )
            notified_3_5 = True

        # Уведомление при +5%
        if change_percent >= 5 and not notified_5:
            await bot.send_message(
                chat_id=OWNER_ID,
                text=f"🚀 Монета *{coin_id}* достигла цели +5%!\n\nТекущая цена: ${current_price:.4f}",
                parse_mode="Markdown"
            )
            notified_5 = True

        # Уведомление, если прошло 12 часов и нет +3.5%
        elapsed = time.time() - start_data["start_time"]
        if elapsed >= 43200 and not notified_timeout:  # 12 часов
            await bot.send_message(
                chat_id=OWNER_ID,
                text=f"⏱ С момента отслеживания монеты *{coin_id}* прошло 12 часов.\n\nИзменение цены: {change_percent:+.2f}%\nТекущая цена: ${current_price:.4f}",
                parse_mode="Markdown"
            )
            notified_timeout = True
            return  # Завершаем отслеживание

        # Завершаем отслеживание, если достигнут +5%
        if notified_5:
            return
