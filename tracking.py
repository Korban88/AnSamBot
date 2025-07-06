import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

from aiogram import Bot

from config import NOTIFICATION_INTERVAL_SECONDS, TRACKING_FILE, TARGET_PROFIT_PERCENT
from crypto_utils import get_current_price

logger = logging.getLogger(__name__)

tracking_tasks = {}

def load_tracking_data():
    if not os.path.exists(TRACKING_FILE):
        return {}
    with open(TRACKING_FILE, 'r') as f:
        return json.load(f)

def save_tracking_data(data):
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)

async def start_tracking(bot: Bot, user_id: int, symbol: str, entry_price: float):
    logger.info(f"🚀 Запуск отслеживания монеты: {symbol} по цене {entry_price}")
    tracking_data = load_tracking_data()
    tracking_data[symbol] = {
        "user_id": user_id,
        "symbol": symbol,
        "entry_price": entry_price,
        "start_time": datetime.utcnow().isoformat()
    }
    save_tracking_data(tracking_data)

    async def check_price():
        try:
            while True:
                current_price = await get_current_price(symbol)
                if current_price is None:
                    await asyncio.sleep(NOTIFICATION_INTERVAL_SECONDS)
                    continue

                growth = (current_price - entry_price) / entry_price * 100
                logger.info(f"📈 [{symbol}] Цена: {current_price} ({growth:.2f}% от входа)")

                if growth >= TARGET_PROFIT_PERCENT:
                    await bot.send_message(user_id, f"✅ {symbol.upper()} выросла на {growth:.2f}% с момента отслеживания.")
                    tracking_tasks.pop(symbol, None)
                    tracking_data.pop(symbol, None)
                    save_tracking_data(tracking_data)
                    break

                start_time = datetime.fromisoformat(tracking_data[symbol]["start_time"])
                if datetime.utcnow() - start_time > timedelta(hours=12):
                    await bot.send_message(user_id, f"⏱ Прошло 12 часов, {symbol.upper()} изменилась на {growth:.2f}%.")
                    tracking_tasks.pop(symbol, None)
                    tracking_data.pop(symbol, None)
                    save_tracking_data(tracking_data)
                    break

                await asyncio.sleep(NOTIFICATION_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info(f"❌ Отслеживание отменено: {symbol}")
        except Exception as e:
            logger.error(f"⚠️ Ошибка в отслеживании {symbol}: {e}")

    task = asyncio.create_task(check_price())
    tracking_tasks[symbol] = task

async def stop_all_tracking():
    for task in tracking_tasks.values():
        task.cancel()
    tracking_tasks.clear()
    if os.path.exists(TRACKING_FILE):
        os.remove(TRACKING_FILE)
    logger.info("🛑 Все отслеживания остановлены")
