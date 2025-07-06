import asyncio
import logging
import json
from datetime import datetime, timedelta
from crypto_utils import get_current_price
from config import NOTIFICATION_INTERVAL_SECONDS, TRACKING_FILE
from aiogram import Bot

bot = Bot(token="8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c")

tracking_data = {}

def save_tracking_data():
    with open(TRACKING_FILE, "w") as f:
        json.dump(tracking_data, f)

def load_tracking_data():
    global tracking_data
    try:
        with open(TRACKING_FILE, "r") as f:
            tracking_data = json.load(f)
    except FileNotFoundError:
        tracking_data = {}

async def track_coin(user_id, coin_id, entry_price):
    start_time = datetime.now()
    logging.info(f"🚀 Старт отслеживания {coin_id} для {user_id} с цены {entry_price}")

    while True:
        await asyncio.sleep(NOTIFICATION_INTERVAL_SECONDS)
        current_price = await get_current_price(coin_id)
        if current_price is None:
            logging.warning(f"⚠️ Не удалось получить цену для {coin_id}")
            continue

        price_change_percent = (current_price - entry_price) / entry_price * 100
        elapsed_time = datetime.now() - start_time

        if price_change_percent >= 5:
            await bot.send_message(user_id, f"🎯 Монета {coin_id} выросла на +5%: {current_price:.4f} USD")
            break
        elif price_change_percent >= 3.5:
            await bot.send_message(user_id, f"📈 Монета {coin_id} выросла на +3.5%: {current_price:.4f} USD")
        elif elapsed_time >= timedelta(hours=12):
            await bot.send_message(
                user_id,
                f"⏱ За 12 часов монета {coin_id} изменилась на {price_change_percent:.2f}%. "
                f"Текущая цена: {current_price:.4f} USD"
            )
            break

async def start_tracking(coin_id, user_id):
    current_price = await get_current_price(coin_id)
    if current_price is None:
        logging.warning(f"⚠️ Не удалось получить цену для {coin_id}")
        return

    user_id_str = str(user_id)
    tracking_data[user_id_str] = {
        "coin_id": coin_id,
        "entry_price": current_price,
        "start_time": datetime.now().isoformat()
    }
    save_tracking_data()

    asyncio.create_task(track_coin(user_id, coin_id, current_price))

def stop_all_tracking(user_id):
    user_id_str = str(user_id)
    if user_id_str in tracking_data:
        del tracking_data[user_id_str]
        save_tracking_data()
        logging.info(f"🛑 Остановлено отслеживание для {user_id}")
    else:
        logging.info(f"❌ Нет активных отслеживаний для {user_id}")
