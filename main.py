import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from core.database import Database
from utils.scheduler import setup_scheduler
from handlers import register_handlers

# --- Конфигурация логов ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Проверка окружения ---
def validate_environment():
    """Проверяет обязательные переменные окружения с подробным логированием."""
    required_vars = {
        'TELEGRAM_TOKEN': {
            'value': os.getenv("TELEGRAM_TOKEN"),
            'hint': "Добавьте в Railway Variables или .env файл"
        },
        'OWNER_ID': {
            'value': os.getenv("OWNER_ID"),
            'hint': "Ваш Telegram ID в числовом формате"
        }
    }

    missing_vars = []
    for name, data in required_vars.items():
        if not data['value']:
            missing_vars.append(name)
            logger.error(f"Отсутствует переменная: {name}. Подсказка: {data['hint']}")

    if missing_vars:
        logger.critical("❌ Необходимые переменные окружения не найдены!")
        exit(1)

    logger.info("✅ Все переменные окружения загружены корректно")

# --- Инициализация бота ---
def initialize_bot():
    """Инициализирует бота с обработкой ошибок"""
    try:
        bot = Bot(
            token=os.getenv("TELEGRAM_TOKEN"),
            parse_mode="HTML"
        )
        dp = Dispatcher(bot, storage=MemoryStorage())
        return bot, dp
    except Exception as e:
        logger.critical(f"Ошибка инициализации бота: {str(e)}", exc_info=True)
        exit(1)

# --- Жизненный цикл ---
async def on_startup(dp):
    """Действия при запуске"""
    try:
        await dp.bot.send_message(
            os.getenv("OWNER_ID"),
            "🟢 Бот успешно запущен!\n"
            f"ID: {os.getenv('OWNER_ID')}\n"
            f"Токен: {'установлен' if os.getenv('TELEGRAM_TOKEN') else 'отсутствует'}"
        )
        logger.info("Бот запущен и готов к работе")
    except Exception as e:
        logger.error(f"Ошибка уведомления о запуске: {e}")

async def on_shutdown(dp):
    """Действия при остановке"""
    try:
        await dp.bot.send_message(os.getenv("OWNER_ID"), "🔴 Бот остановлен!")
        logger.warning("Завершение работы бота")
    except Exception as e:
        logger.error(f"Ошибка уведомления об остановке: {e}")
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()

# --- Главная функция ---
def main():
    validate_environment()  # Валидация переменных
    
    try:
        bot, dp = initialize_bot()
        db = Database()  # Инициализация БД

        register_handlers(dp)  # Регистрация обработчиков
        setup_scheduler(bot)   # Планировщик задач

        # Запуск поллинга
        executor.start_polling(
            dp,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True
        )
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}", exc_info=True)
        exit(1)

if __name__ == '__main__':
    main()
