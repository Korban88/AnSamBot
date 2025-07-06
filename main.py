import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from core.database import Database
from utils.scheduler import setup_scheduler
from core.signal_generator import generate_top_signals
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

async def on_startup(dp):
    logger.info("Бот запущен")
    await dp.bot.send_message(os.getenv("OWNER_ID"), "🟢 Бот успешно запущен")

async def on_shutdown(dp):
    logger.warning("Бот остановлен")
    await dp.bot.send_message(os.getenv("OWNER_ID"), "🔴 Бот остановлен")

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    dp = Dispatcher(bot, storage=MemoryStorage())
    db = Database()

    # Регистрация обработчиков
    register_handlers(dp)
    
    # Планировщик ежедневных сигналов
    setup_scheduler(bot)

    # Запуск
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )

if __name__ == '__main__':
    main()
