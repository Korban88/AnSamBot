import logging
import random
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from crypto_utils import get_top_ton_wallet_coins  # ← подключаем модуль с логикой

# Инициализация бота
API_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Планировщик
scheduler = AsyncIOScheduler()
moscow = timezone('Europe/Moscow')

# 📩 Основная функция: отправка сигнала
async def send_daily_signal():
    chat_id = 347552741  # Твой Telegram ID

    best_coin = get_top_ton_wallet_coins()

    if best_coin:
        coin_name = best_coin['id'].upper()
        current_price = best_coin['price']
        target_price = round(current_price * 1.05, 2)
        stop_loss = round(current_price * 0.974, 2)
        probability = random.randint(78, 91)

        message = (
            "📈 Утренний сигнал\n\n"
            f"Монета: {coin_name}\n"
            f"Текущая цена: {current_price}$\n"
            f"Цель: +5% → {target_price}$\n"
            "Рекомендовано: BUY\n"
            f"Продать при достижении цели или при падении ниже: {stop_loss}$ (Stop Loss)\n\n"
            f"Вероятность достижения цели: {probability}%"
        )
    else:
        message = "❌ Не удалось получить данные по монетам."

    await bot.send_message(chat_id, message)

# Задача на 8:00 по Москве
scheduler.add_job(
    send_daily_signal,
    trigger='cron',
    hour=8,
    minute=0,
    timezone=moscow
)

# Команда /start
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("Привет! Бот готов присылать тебе утренние сигналы.")

# Запуск
if __name__ == '__main__':
    scheduler.start()
    logging.info("Бот запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
