import logging
from aiogram import Bot, Dispatcher, executor, types
from config import get_config

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('AnSamBot')

bot = Bot(token="8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c", parse_mode="HTML")
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    cfg = get_config()
    await message.reply(
        f"🤖 AnSamBot v{cfg['version']}\n"
        f"• Owner: {cfg['owner']}\n"
        f"• Mode: {cfg['mode'].upper()}\n"
        f"• DB: {'✅' if cfg['db_status'] else '❌'}"
    )

if __name__ == '__main__':
    logger.info("🚀 Starting production bot")
    executor.start_polling(dp, skip_updates=True)
