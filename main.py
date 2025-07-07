import os
import logging
from aiogram import Bot, Dispatcher, executor, types

# --- Жёсткая инициализация ---
TELEGRAM_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"  # Ваш токен
OWNER_ID = 347552741  # Ваш ID

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("🚀 Бот работает в аварийном режиме!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
