import logging
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from datetime import datetime
import asyncio

# Инициализация бота
API_TOKEN = 8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Планировщик
scheduler = AsyncIOScheduler()
moscow = timezone('Europe/Moscow')

# 📩 Функция отправки сигнала
async def send_daily_signal():
    chat_id = 347552741  # Замени на свой Telegram ID или добавь получение из базы
    await bot.send_message(chat_id, "📈 Утренний сигнал: BUY BNB — цель: +5.0%")

# Задача: запуск каждый день в 8:00 по Москве
scheduler.add_job(
    send_daily_signal,
    trigger='cron',
    hour=8,
    minute=0,
    timezone=moscow
)

# Команда старт
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("Привет! Бот готов присылать тебе утренние сигналы.")

# Запуск
if __name__ == '__main__':
    scheduler.start()
    logging.info("Бот запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
