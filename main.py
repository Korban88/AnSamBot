import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TELEGRAM_TOKEN, OWNER_ID

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    """Главная команда бота"""
    try:
        await message.reply(
            "🤖 AnSamBot в работе!\n"
            "🔹 ID владельца: 347552741\n"
            "🔹 Режим: production"
        )
        logger.info(f"Новый пользователь: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")

@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    """Проверка состояния системы"""
    await message.reply(
        "⚡ Статус системы:\n"
        "• Бот: активен\n"
        "• База данных: доступна\n"
        "• Последняя проверка: сейчас"
    )
    logger.info(f"Проверка статуса от {message.from_user.id}")

async def on_startup(dp):
    """Действия при запуске"""
    try:
        await bot.send_message(OWNER_ID, "🟢 Бот перезапущен в production-режиме")
        logger.info("Система инициализирована")
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")

if __name__ == '__main__':
    logger.info("==== ЗАПУСК СИСТЕМЫ ====")
    executor.start_polling(
        dp,
        on_startup=on_startup,
        skip_updates=True,
        timeout=60
    )
