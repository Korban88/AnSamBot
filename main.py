import os
import logging
from aiogram import Bot, Dispatcher, executor, types

# Жёсткая инициализация
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

if not TOKEN or not OWNER_ID:
    logging.critical("❌ Переменные окружения не загружены!")
    exit(1)

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

@dp.message_handler(commands=['env'])
async def check_env(message: types.Message):
    """Проверка переменных окружения"""
    await message.reply(
        f"TOKEN: {'✅' if TOKEN else '❌'}\n"
        f"OWNER_ID: {OWNER_ID or '❌'}"
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
