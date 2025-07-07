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

# Проверка источника переменных
if TELEGRAM_TOKEN == "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c":
    logger.warning("⚠️ ВНИМАНИЕ: Используется fallback-значение для токена!")
else:
    logger.info("✅ Токен загружен из переменных окружения")

if OWNER_ID == "347552741":
    logger.warning("⚠️ ВНИМАНИЕ: Используется fallback-значение для OWNER_ID!")
else:
    logger.info("✅ OWNER_ID загружен из переменных окружения")

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    """Обработчик команды /start"""
    try:
        await message.reply(
            f"🤖 Бот работает!\n"
            f"ID владельца: {OWNER_ID}\n"
            f"Используется {'fallback' if TELEGRAM_TOKEN == '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c' else 'Railway'} токен"
        )
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")

@dp.message_handler(commands=['env'])
async def show_env(message: types.Message):
    """Показать текущие настройки окружения"""
    await message.reply(
        f"Текущая конфигурация:\n"
        f"Токен: {'fallback' if TELEGRAM_TOKEN == '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c' else 'Railway'}\n"
        f"OWNER_ID: {OWNER_ID}\n"
        f"Источник: {'код' if OWNER_ID == '347552741' else 'Railway'}"
    )

@dp.message_handler(commands=['ping'])
async def ping(message: types.Message):
    """Health-check"""
    await message.reply("🏓 Pong! Бот работает стабильно")
    logger.info(f"Health-check от {message.from_user.id}")

async def on_startup(dp):
    """Действия при запуске"""
    try:
        await bot.send_message(OWNER_ID, "🟢 Бот успешно запущен")
        logger.info("Уведомление о запуске отправлено владельцу")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")

if __name__ == '__main__':
    try:
        logger.info("Запуск бота...")
        executor.start_polling(
            dp,
            on_startup=on_startup,
            skip_updates=True,
            timeout=60,
            relax=0.5
        )
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
    finally:
        logger.warning("Бот остановлен")
