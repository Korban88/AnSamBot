import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID
from analysis import analyze_cryptos
from tracking import start_tracking, stop_all_tracking, tracking_loop
from signal_utils import get_next_signal_message, reset_signal_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.MARKDOWN_V2)
dp = Dispatcher(bot)

# Кнопки меню
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("Получить ещё сигнал"),
    KeyboardButton("Остановить все отслеживания")
)

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def handle_next_signal(message: types.Message):
    signal_message, coin_id, entry_price = get_next_signal_message()
    await message.answer(signal_message, parse_mode=types.ParseMode.MARKDOWN_V2)

    if coin_id and entry_price:
        start_tracking(coin_id, message.from_user.id, entry_price)

@dp.message_handler(lambda message: message.text == "Остановить все отслеживания")
async def handle_stop_tracking(message: types.Message):
    stop_all_tracking()
    await message.answer("🛑 Все отслеживания остановлены.")

async def on_startup(dispatcher):
    asyncio.create_task(tracking_loop(bot))
    logger.info("📡 Бот запущен и отслеживание активировано.")

if __name__ == '__main__':
    reset_signal_index()
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
