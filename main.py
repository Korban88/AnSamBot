import logging
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from datetime import datetime
import asyncio

# Инициализация бота
API_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Планировщик
scheduler = AsyncIOScheduler()
moscow = timezone('Europe/Moscow')

# 📩 Функция отправки сигнала (временно с фиктивными данными)
async def send_daily_signal():
    chat_id = 347552741  # Твой Telegram ID

    # Примерные данные (в будущем заменим на анализ)
    coin = "BNB"
    current_price = 612.30
    target_price = round(current_price * 1.05, 2)
    stop_loss = round(current_price * 0.974, 2)  # -2.6% запас

    message = (
        "📈 Утренний сигнал\n\n"
        f"Монета: {coin}\n"
        f"Текущая цена: {current_price}$\n"
        f"Цель: +5% → {target_price}$\n"
        "Рекомендовано: BUY\n"
        f"Продать при достижении цели или при падении ниже: {stop_loss}$ (Stop Loss)"
    )

    await bot.send_message(chat_id, message)

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
