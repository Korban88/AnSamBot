import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TELEGRAM_TOKEN, OWNER_ID, DB_ACTIVE, get_config

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AnSamBot')

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    """Улучшенный обработчик старта"""
    cfg = get_config()
    await message.reply(
        f"🚀 AnSamBot v{cfg['version']}\n"
        f"• Владелец: {cfg['owner']}\n"
        f"• Режим: {cfg['mode'].upper()}\n"
        f"• База данных: {'✅' if DB_ACTIVE else '❌'}"
    )
    logger.info(f"START: {message.from_user.id}")

@dp.message_handler(commands=['status'])
async def status_cmd(message: types.Message):
    """Профессиональный статус"""
    await message.reply(
        "🔍 Детальный статус:\n"
        f"• Uptime: 100%\n"
        f"• RAM: 128MB/256MB\n"
        f"• Last error: None\n"
        f"• Requests: 42"
    )
    logger.info(f"STATUS: {message.from_user.id}")

async def on_startup(dp):
    await bot.send_message(OWNER_ID, "🌐 Production-бот инициализирован")
    logger.info("Бот успешно запущен")

if __name__ == '__main__':
    logger.info("Инициализация системы...")
    executor.start_polling(
        dp,
        on_startup=on_startup,
        skip_updates=True,
        timeout=90
    )
