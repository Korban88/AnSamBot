import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time, timedelta
from keep_alive import keep_alive
from signals import get_crypto_signal

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Проверка токена
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения.")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Клавиатура
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Получить ещё сигнал"))
keyboard.add(KeyboardButton("Что-то пошло не так"))

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer("Бот работает и готов присылать крипто-сигналы.", reply_markup=keyboard)

# Обработчик кнопок
@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def more_signal_handler(message: types.Message):
    signal = get_crypto_signal()
    text = f"💹 Сигнал: {signal['action']} {signal['coin']} — цель: +{signal['target_profit_percent']}%"
    await message.answer(text)

@dp.message_handler(lambda message: message.text == "Что-то пошло не так")
async def error_handler(message: types.Message):
    await message.answer("Если возникла ошибка — просто напиши Артуру Корбану или попробуй позже.")

# Ежедневная рассылка сигнала
async def send_daily_signal():
    if CHAT_ID:
        signal = get_crypto_signal()
        text = f"📈 Утренний сигнал: {signal['action']} {signal['coin']} — цель: +{signal['target_profit_percent']}%"
        await bot.send_message(CHAT_ID, text)

# Планировщик
scheduler = AsyncIOScheduler()
moscow_time = time(hour=8, minute=0)
now = datetime.now()
first_run = datetime.combine(now.date(), moscow_time)
if now > first_run:
    first_run += timedelta(days=1)

scheduler.add_job(send_daily_signal, "interval", days=1, start_date=first_run)
scheduler.start()

# Стартуем
if __name__ == "__main__":
    keep_alive()
    from aiogram import executor
    logging.info("Бот запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
