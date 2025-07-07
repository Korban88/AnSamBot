import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import config  # Импорт из нового файла

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=config.TELEGRAM_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("🤖 Бот работает корректно!")

@dp.message_handler(commands=['ping'])
async def ping(message: types.Message):
    await message.reply("🏓 Pong! Система стабильна")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
