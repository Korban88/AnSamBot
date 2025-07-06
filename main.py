import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import TELEGRAM_TOKEN, OWNER_ID
from crypto_list import get_all_cryptos
from analysis import analyze_cryptos
from signal_utils import get_next_signal_message, reset_signal_index
from tracking import start_tracking, stop_all_tracking

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode=types.ParseMode.MARKDOWN_V2)
dp = Dispatcher(bot)

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Получить ещё сигнал"))
keyboard.add(KeyboardButton("Остановить все отслеживания"))

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def handle_get_signal(message: types.Message):
    logger.info("📩 Получен запрос на сигнал")
    cryptos = get_all_cryptos()
    results = await analyze_cryptos(cryptos)

    if not results:
        await message.answer("🚫 Нет подходящих монет сейчас. Попробуй позже.")
        return

    signal = get_next_signal_message(results)
    if signal:
        await message.answer(signal, reply_markup=keyboard)
    else:
        await message.answer("⚠️ Не удалось сгенерировать новый сигнал.")

@dp.message_handler(lambda message: message.text == "Остановить все отслеживания")
async def stop_tracking(message: types.Message):
    stop_all_tracking()
    await message.answer("⛔️ Все отслеживания остановлены.", reply_markup=keyboard)

async def send_daily_signal():
    await bot.wait_until_ready()
    while True:
        now = asyncio.get_event_loop().time()
        next_run = ((now // 86400) + 1) * 86400 + 8 * 3600  # 8:00 МСК
        await asyncio.sleep(max(0, next_run - now))

        cryptos = get_all_cryptos()
        results = await analyze_cryptos(cryptos)

        if results:
            reset_signal_index()
            signal = get_next_signal_message(results)
            if signal:
                await bot.send_message(chat_id=OWNER_ID, text=signal, reply_markup=keyboard)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(send_daily_signal())
    executor.start_polling(dp, skip_updates=True)
