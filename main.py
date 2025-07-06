import logging
import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from config import TELEGRAM_TOKEN, OWNER_ID
from analysis import analyze_cryptos
from tracking import start_tracking, stop_all_tracking
from signal_utils import get_next_signal_message, reset_signal_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("Получить ещё сигнал"))
main_keyboard.add(KeyboardButton("Остановить все отслеживания"))

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=main_keyboard)

@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def handle_get_signal(message: types.Message):
    try:
        signal_text, coin_id = await get_next_signal_message()
        if signal_text:
            inline_kb = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Следить за монетой", callback_data=f"track:{coin_id}")
            )
            await message.answer(signal_text, reply_markup=inline_kb, parse_mode="MarkdownV2")
        else:
            await message.answer("❌ Нет подходящих монет для сигнала.")
    except Exception as e:
        logger.error(f"Ошибка при отправке сигнала: {e}")
        await message.answer("⚠️ Ошибка при генерации сигнала.")

@dp.message_handler(lambda message: message.text == "Остановить все отслеживания")
async def handle_stop_tracking(message: types.Message):
    stop_all_tracking()
    await message.answer("🛑 Все отслеживания остановлены.")

@dp.callback_query_handler(lambda c: c.data.startswith("track:"))
async def handle_track_callback(callback_query: types.CallbackQuery):
    coin_id = callback_query.data.split("track:")[1]
    start_tracking(coin_id, bot, OWNER_ID)
    await callback_query.answer("Монета добавлена в отслеживание.")

async def scheduled_signal():
    await bot.send_message(OWNER_ID, "⏰ Ежедневный сигнал начинается")
    signal_text, coin_id = await get_next_signal_message()
    if signal_text:
        inline_kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Следить за монетой", callback_data=f"track:{coin_id}")
        )
        await bot.send_message(OWNER_ID, signal_text, reply_markup=inline_kb, parse_mode="MarkdownV2")

async def scheduler():
    while True:
        now = asyncio.get_event_loop().time()
        target_time = 8 * 3600  # 8:00 МСК
        current_time = (now + 3 * 3600) % 86400  # МСК
        delay = (target_time - current_time) % 86400
        await asyncio.sleep(delay)
        await scheduled_signal()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    executor.start_polling(dp, skip_updates=True)
