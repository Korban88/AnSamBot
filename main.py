import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# --- Инициализация ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Загрузка конфигурации ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

if not TOKEN or not OWNER_ID:
    logger.critical("❌ Не найдены обязательные переменные окружения!")
    exit(1)

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# --- Health-check ---
@dp.message_handler(commands=['ping'])
async def ping(message: types.Message):
    """Проверка работоспособности бота"""
    await message.reply("🏓 Pong! Бот активен")
    logger.info(f"Health-check от пользователя {message.from_user.id}")

# --- Основные команды ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(
        "🤖 Бот успешно запущен!\n"
        "Используйте /ping для проверки работоспособности"
    )

# --- Жизненный цикл ---
async def on_startup(dp):
    try:
        await bot.send_message(OWNER_ID, "🟢 Бот успешно запущен")
        logger.info("Уведомление о запуске отправлено")
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")

async def on_shutdown(dp):
    try:
        await bot.send_message(OWNER_ID, "🔴 Бот остановлен")
        logger.warning("Уведомление об остановке отправлено")
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()

if __name__ == '__main__':
    try:
        executor.start_polling(
            dp,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            reset_webhook=True,
            timeout=60,
            relax=0.5
        )
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        exit(1)import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types

# Конфигурация
TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"  # Пока оставляем хардкод
OWNER_ID = 347552741

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("🤖 Бот работает в штатном режиме!")

async def on_startup(_):
    await bot.send_message(OWNER_ID, "🔵 Бот перезапущен")

if __name__ == '__main__':
    # Важные параметры для поллинга
    executor.start_polling(
        dp,
        on_startup=on_startup,
        skip_updates=True,
        timeout=60,
        relax=1,
        reset_webhook=True
    )
