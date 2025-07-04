import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

# Простой inline-клавиатурный блок
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add("🚀 Получить ещё сигнал", "🟢 Старт")

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("Бот запущен", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "🟢 Старт")
async def start_message(message: types.Message):
    await message.answer("Ты нажал Старт")

@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def signal_message(message: types.Message):
    await message.answer("Ты запросил сигнал")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)
