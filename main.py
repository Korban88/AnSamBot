import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from core.database import Database
from utils.scheduler import schedule_daily_signal
from handlers import register_handlers

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="bot.log"
)

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher(bot)
db = Database()

# Регистрация команд
register_handlers(dp)

if __name__ == "__main__":
    schedule_daily_signal(bot)  # Запуск ежедневных сигналов
    executor.start_polling(dp, skip_updates=True)
