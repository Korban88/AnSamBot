import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from keep_alive import keep_alive
from utils import get_crypto_signal

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Получаем токен и chat_id из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Планировщик задач
scheduler = AsyncIOScheduler()

# Задача — отправка сигнала каждый день в 08:00 по МСК
def send_daily_signal():
    signal = get_crypto_signal()
    message = f"📈 Утренний сигнал: {signal}"
    try:
        asyncio.create_task(bot.send_message(chat_id=CHAT_ID, text=message))
        logging.info("Утренний сигнал отправлен")
    except Exception as e:
        logging.error(f"Ошибка при отправке сигнала: {e}")

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def send_welcome(message: Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!")

# Главная функция
async def on_startup(_):
    logging.info("Бот запущен и готов к работе.")
    scheduler.add_job(send_daily_signal, 'cron', hour=8, minute=0, timezone='Europe/Moscow')
    scheduler.start()

if __name__ == "__main__":
    import asyncio
    keep_alive()  # Запускаем Flask-сервер
    executor.start_polling(dp, on_startup=on_startup)
