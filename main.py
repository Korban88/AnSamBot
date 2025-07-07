import os
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
