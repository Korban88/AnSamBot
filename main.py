import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from core.database import Database
from utils.scheduler import setup_scheduler
from handlers import register_handlers

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

# --- Проверка переменных окружения ---
def check_env():
    """Проверяет обязательные переменные окружения."""
    required_vars = {
        'TELEGRAM_TOKEN': os.getenv("TELEGRAM_TOKEN"),
        'OWNER_ID': os.getenv("OWNER_ID")
    }
    missing_vars = [name for name, value in required_vars.items() if not value]
    
    if missing_vars:
        logger.critical(f"Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        exit(1)

# --- Действия при запуске/остановке ---
async def on_startup(dp):
    try:
        await dp.bot.send_message(os.getenv("OWNER_ID"), "🟢 Бот успешно запущен!")
        logger.info("Бот запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")

async def on_shutdown(dp):
    try:
        await dp.bot.send_message(os.getenv("OWNER_ID"), "🔴 Бот остановлен!")
        logger.warning("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при остановке: {e}")

# --- Основная функция ---
def main():
    check_env()  # Проверяем переменные перед запуском
    
    try:
        bot = Bot(token=os.getenv("TELEGRAM_TOKEN"), parse_mode="HTML")  # Добавлен parse_mode
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
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)  # Добавлено exc_info для трейсбэка

if __name__ == '__main__':
    main()
