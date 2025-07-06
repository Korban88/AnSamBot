import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID
from analysis import analyze_cryptos
from tracking import start_tracking, stop_all_tracking
from signal_utils import get_next_signal_message, reset_signal_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Клавиатура
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("Получить ещё сигнал"),
    KeyboardButton("Остановить все отслеживания"),
)

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    if message.from_user.id != TELEGRAM_USER_ID:
        return
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)
    reset_signal_index()
    signal_message, coin_id, entry_price = await get_next_signal_message()
    await message.answer(signal_message)
    await start_tracking(coin_id, entry_price)

@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def handle_more_signal(message: types.Message):
    if message.from_user.id != TELEGRAM_USER_ID:
        return
    signal_message, coin_id, entry_price = await get_next_signal_message()
    if signal_message:
        await message.answer(signal_message)
        await start_tracking(coin_id, entry_price)
    else:
        await message.answer("Нет новых сигналов. Попробуйте позже.")

@dp.message_handler(lambda message: message.text == "Остановить все отслеживания")
async def handle_stop_tracking(message: types.Message):
    if message.from_user.id != TELEGRAM_USER_ID:
        return
    await stop_all_tracking()
    await message.answer("⛔ Все отслеживания остановлены.")

if __name__ == '__main__':
    logger.info("📡 Бот запущен и отслеживание активировано.")
    from tracking import tracking_loop
    import asyncio
    asyncio.create_task(tracking_loop())
    executor.start_polling(dp, skip_updates=True)
