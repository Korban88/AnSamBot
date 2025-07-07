import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from core.database import Database
from utils.scheduler import setup_scheduler
from handlers import register_handlers  # Убедитесь, что файл handlers.py существует

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def on_startup(dp):
    """Действия при запуске бота"""
    try:
        await dp.bot.send_message(os.getenv("OWNER_ID"), "🟢 Бот успешно запущен")
        logger.info("Бот запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")

async def on_shutdown(dp):
    """Действия при остановке бота"""
    try:
        await dp.bot.send_message(os.getenv("OWNER_ID"), "🔴 Бот остановлен")
        logger.warning("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при остановке: {e}")

def main():
    try:
        bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
        dp = Dispatcher(bot, storage=MemoryStorage())
        db = Database()  # Инициализация БД

        register_handlers(dp)  # Регистрация команд
        setup_scheduler(bot)   # Настройка расписания

        executor.start_polling(
            dp,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True
        )
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")

if __name__ == '__main__':
    main()
