import logging
from aiogram import Bot, Dispatcher, executor, types
from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler()]
)

cfg = get_config()
bot = Bot(token=cfg['token'], parse_mode="HTML")
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(
        f"🤖 AnSamBot v{cfg['version']}\n"
        f"• Режим: {cfg['mode']}\n"
        f"• DB: {'✅' if cfg['db_status'] else '❌'}"
    )

@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    await message.reply("🟢 Бот активен")
    logging.info(f"Status checked by {message.from_user.id}")

if __name__ == '__main__':
    logging.info("==== STARTING BOT ====")
    try:
        executor.start_polling(
            dp,
            skip_updates=True,
            timeout=60,
            relax=0.5
        )
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
