import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from crypto_utils import get_top_coins
from signal_formatter import format_signal
from tracker import CoinTracker
from keep_alive import keep_alive

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
tracker = CoinTracker(bot, USER_ID)

logging.basicConfig(level=logging.INFO)
scheduler = AsyncIOScheduler()

# Сохранение очереди монет
signal_queue = []

def schedule_daily_signal():
    now = datetime.now()
    next_run = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    delta = next_run - now
    minutes = delta.total_seconds() // 60
    logging.info(f"⏳ До следующего сигнала: {minutes} минут")
    scheduler.add_job(send_daily_signal, "interval", days=1, start_date=next_run)

async def send_daily_signal():
    top_coins = await get_top_coins()
    if not top_coins:
        await bot.send_message(USER_ID, "⚠️ Не удалось получить сигнал.")
        return

    signal_queue.clear()
    signal_queue.extend(top_coins)

    coin_data = signal_queue.pop(0)
    text = format_signal(coin_data)
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(f"👁 Следить за {coin_data['coin']}", callback_data=f"track:{coin_data['coin']}:{coin_data['price']}")
    )
    await bot.send_message(USER_ID, text, reply_markup=keyboard)

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!")

@dp.message_handler(lambda m: m.text == "Получить ещё сигнал")
async def send_signals(message: types.Message):
    logging.info("Нажата кнопка 'Получить ещё сигнал'")
    if not signal_queue:
        top_coins = await get_top_coins()
        if not top_coins:
            await message.answer("⚠️ Не удалось получить сигнал.")
            return
        signal_queue.extend(top_coins)

    coin_data = signal_queue.pop(0)
    text = format_signal(coin_data)
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(f"👁 Следить за {coin_data['coin']}", callback_data=f"track:{coin_data['coin']}:{coin_data['price']}")
    )
    await message.answer(text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("track:"))
async def handle_tracking(callback_query: types.CallbackQuery):
    _, coin_id, entry_price = callback_query.data.split(":")
    tracker.start_tracking(coin_id, float(entry_price))
    await callback_query.answer()
    await bot.send_message(USER_ID, f"📡 Монета <b>{coin_id}</b> добавлена в отслеживание.\nБот сообщит при +3.5% и +5%.")

@dp.message_handler(lambda m: m.text == "Остановить все отслеживания")
async def stop_tracking(message: types.Message):
    tracker.stop_all_tracking()
    await message.answer("⛔️ Все отслеживания остановлены.")

if __name__ == "__main__":
    keep_alive()
    scheduler.start()
    tracker.run()
    schedule_daily_signal()
    logging.info("Бот запущен и готов.")
    executor.start_polling(dp, skip_updates=True)
