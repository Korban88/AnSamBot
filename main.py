import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from utils import get_crypto_signal
from keep_alive import keep_alive

# Токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Основной сигнал
async def send_morning_signal():
    signal = get_crypto_signal()
    await bot.send_message(347552741, signal)

# Команды
@dp.message(commands=['start', 'test'])
async def start_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Получить ещё сигнал", callback_data="more_signal")]
    ])
    await message.answer(
        "Добро пожаловать в новую жизнь, Корбан!\nAnSam Bot подключён. Первый сигнал придёт в 8:00 по Москве.",
        reply_markup=kb
    )

@dp.callback_query()
async def handle_callbacks(callback: types.CallbackQuery):
    if callback.data == "more_signal":
        signal = get_crypto_signal()
        await callback.message.answer(signal)

# Планировщик
scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
scheduler.add_job(send_morning_signal, trigger='cron', hour=8, minute=0)

# Запуск
async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
