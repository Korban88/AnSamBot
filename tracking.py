import json
import os
import time
from datetime import datetime
from aiogram import Bot

from config import NOTIFICATION_INTERVAL_SECONDS, TRACKING_FILE, GROWTH_THRESHOLD_PERCENT, TARGET_PROFIT_PERCENT
from crypto_utils import get_current_price

# Загрузка активных трекингов
def load_tracking_data():
    if not os.path.exists(TRACKING_FILE):
        return {}
    with open(TRACKING_FILE, 'r') as f:
        return json.load(f)

# Сохранение трекингов
def save_tracking_data(data):
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Запустить отслеживание монеты
def start_tracking(coin_id: str, user_id: int, initial_price: float):
    data = load_tracking_data()
    data[coin_id] = {
        'user_id': user_id,
        'start_time': time.time(),
        'initial_price': initial_price
    }
    save_tracking_data(data)

# Остановить все трекинги
def stop_all_tracking():
    save_tracking_data({})

# Асинхронная задача, которая запускается в фоне
async def tracking_loop(bot: Bot):
    while True:
        data = load_tracking_data()
        updated_data = {}
        for coin_id, info in data.items():
            user_id = info['user_id']
            start_time = info['start_time']
            initial_price = info['initial_price']

            current_price = await get_current_price(coin_id)
            if current_price is None:
                continue

            percent_change = ((current_price - initial_price) / initial_price) * 100

            # Уведомление о росте +3.5% или +5%
            if percent_change >= TARGET_PROFIT_PERCENT:
                await bot.send_message(user_id, f"📈 Монета *{coin_id}* выросла на *{percent_change:.2f}%* 🚀", parse_mode='MarkdownV2')
                continue  # не добавляем в updated_data — отслеживание завершено
            elif percent_change >= GROWTH_THRESHOLD_PERCENT:
                await bot.send_message(user_id, f"🔔 *{coin_id}* достигла +{GROWTH_THRESHOLD_PERCENT}% роста \\({percent_change:.2f}%\\)", parse_mode='MarkdownV2')

            # Проверка на 12 часов ожидания
            elapsed_hours = (time.time() - start_time) / 3600
            if elapsed_hours >= 12:
                await bot.send_message(user_id, f"⏰ Прошло 12 часов с начала отслеживания *{coin_id}*. Изменение: *{percent_change:.2f}%*", parse_mode='MarkdownV2')
                continue  # завершено

            updated_data[coin_id] = info

        save_tracking_data(updated_data)
        await asyncio.sleep(NOTIFICATION_INTERVAL_SECONDS)
