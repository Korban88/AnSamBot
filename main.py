import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TELEGRAM_TOKEN, OWNER_ID

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(f"🤖 Бот работает! ID владельца: {OWNER_ID}")

@dp.message_handler(commands=['env'])
async def show_env(message: types.Message):
    await message.reply(
        f"Токен: {'установлен' if TELEGRAM_TOKEN else 'отсутствует'}\n"
        f"OWNER_ID: {OWNER_ID}"
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
