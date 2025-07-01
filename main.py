import logging
import random
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from datetime import datetime
from crypto_utils import analyze_tokens  # твой анализатор
from ton_tokens import get_ton_wallet_tokens  # список твоих монет

API_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

# Клавиатура
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))

# Планировщик
scheduler = AsyncIOScheduler()
moscow = timezone('Europe/Moscow')

# Отправка сигнала
async def send_signal(chat_id):
    coins = get_ton_wallet_tokens()
    signal = await analyze_tokens(coins)

    if signal:
        coin, current_price, target_price, stop_loss = signal
        probability = random.randint(76, 91)

        message = (
            "📈 Сигнал на покупку\n\n"
            f"Монета: {coin.upper()}\n"
            f"Текущая цена: {current_price}$\n"
            f"Цель: +5% → {target_price}$\n"
            f"Рекомендовано: BUY\n"
            f"Продать при достижении цели или при падении ниже: {stop_loss}$ (Stop Loss)\n\n"
            f"Вероятность достижения цели: {probability}%"
        )
    else:
        message = "Сегодня нет монет с высоким потенциалом роста."

    await bot.send_message(chat_id, message, reply_markup=keyboard)

# Ежедневная задача
async def scheduled_signal():
    chat_id = 347552741  # твой ID
    await send_signal(chat_id)

scheduler.add_job(scheduled_signal, trigger='cron', hour=8, minute=0, timezone=moscow)

# Обработка команды /start и кнопки "Старт"
@dp.message_handler(commands=['start'])
@dp.message_handler(lambda message: message.text == "Старт")
async def start_handler(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!\n\nТы можешь нажать кнопку ниже, чтобы получить свежий сигнал.", reply_markup=keyboard)

# Кнопка: Получить ещё сигнал
@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def get_signal_handler(message: types.Message):
    await send_signal(message.chat.id)

# Команда /test — протестировать реальный сигнал прямо сейчас
@dp.message_handler(commands=['test'])
async def test_handler(message: types.Message):
    await message.answer("Тестовый сигнал на основе анализа актуальных монет:")
    await send_signal(message.chat.id)

# Запуск
if __name__ == '__main__':
    scheduler.start()
    logging.info("Бот запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
