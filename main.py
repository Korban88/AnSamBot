import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID
from keyboards import get_main_keyboard
from signal_utils import get_next_signal_message, reset_signal_index
from tracking import start_tracking, stop_all_tracking, tracking_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.MARKDOWN_V2)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    if str(message.from_user.id) != str(TELEGRAM_USER_ID):
        await message.reply("🚫 У вас нет доступа к этому боту.")
        return
    keyboard = get_main_keyboard()
    await message.answer("Добро пожаловать в новую жизнь, Корбан\\!", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def handle_get_signal(message: types.Message):
    signal_message, coin_id, entry_price = await get_next_signal_message()
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="📈 Следить за монетой", callback_data=f"track:{coin_id}:{entry_price}")
    keyboard.add(button)
    await message.answer(signal_message, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('track:'))
async def handle_track_callback(callback_query: types.CallbackQuery):
    _, coin_id, entry_price = callback_query.data.split(':')
    await start_tracking(coin_id, float(entry_price), bot)
    await callback_query.answer(f"⏱ Монета {coin_id} отслеживается")


@dp.message_handler(lambda message: message.text == "Остановить все отслеживания")
async def handle_stop_tracking(message: types.Message):
    await stop_all_tracking(bot)
    await message.answer("🛑 Отслеживание всех монет остановлено")


@dp.message_handler(lambda message: message.text == "Старт")
async def handle_reset_signal_index(message: types.Message):
    reset_signal_index()
    await message.answer("♻️ Индекс сигналов сброшен. Теперь сигналы пойдут сначала.")


if __name__ == '__main__':
    async def on_startup(dp):
        logger.info("📡 Бот запущен и отслеживание активировано.")
        asyncio.create_task(tracking_loop(bot))

if __name__ == "__main__":
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
