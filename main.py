import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import TELEGRAM_TOKEN, OWNER_ID
from signal_utils import get_next_signal_message, reset_signal_index
from tracking import start_tracking, stop_all_tracking

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode=types.ParseMode.MARKDOWN_V2)
dp = Dispatcher(bot)

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("Получить ещё сигнал"))
main_keyboard.add(KeyboardButton("Остановить все отслеживания"))

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ У вас нет доступа к этому боту.")
        return
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=main_keyboard)
    await message.answer("Нажми кнопку ниже, чтобы получить свежий сигнал.", reply_markup=main_keyboard)

@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def handle_next_signal(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    signal_message, coin_id = await get_next_signal_message()
    await message.answer(signal_message, reply_markup=main_keyboard)
    await start_tracking(coin_id, bot)

@dp.message_handler(lambda message: message.text == "Остановить все отслеживания")
async def handle_stop_tracking(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    await stop_all_tracking()
    await message.answer("⛔ Все отслеживания остановлены.", reply_markup=main_keyboard)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
